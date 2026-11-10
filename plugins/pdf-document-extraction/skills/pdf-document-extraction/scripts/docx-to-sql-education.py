#!/usr/bin/env python3
"""
docx-to-sql-education — Parse a structured flashcard docx (track →
module → set → card / micro-quiz) and emit a SQL migration that
re-seeds an education curriculum.

Designed for the the target platform education curriculum tables:
  - public.education_tracks
  - public.education_modules
  - public.education_lessons
  - public.education_lesson_sections  (kind='flashcard')
  - public.education_quizzes          (scope='lesson')
  - public.education_quiz_questions

USAGE:
  1. Update DOC_PATH and SLUG_PREFIX constants below
  2. Update the SQL emit_*() functions if your schema differs
  3. python3 docx-to-sql-education.py > 20260910_<topic>.sql
  4. paste the output into Supabase Studio SQL editor

For a different schema, swap the emit_set() / emit_quiz() functions
to write whatever INSERTs you need. The parser + structure (modules /
sets / cards / quizzes) is the reusable part.

KEY PARSER DETAILS — see
skills/productivity/document-processing/references/docx-run-level-extraction.md
"""
import re
from docx import Document

# ────────────────────────────────────────────────────────────────────
# CONFIG — set these for your docx
# ────────────────────────────────────────────────────────────────────
DOC_PATH = '/path/to/your-flashcards.docx'
TRACK_TO_DB_SLUG = {
    'foundations': 'foundations',
    'charting': 'charting',
    'risk': 'risk',
    'live': 'live',  # repurposed as Intermediate Concepts & Psychology
}


def slugify(text: str) -> str:
    text = re.sub(r'[^a-zA-Z0-9\s-]', '', text.lower())
    return re.sub(r'\s+', '-', text).strip('-')


# ────────────────────────────────────────────────────────────────────
# PARSER — walk the docx, identify sections by content shape
# ────────────────────────────────────────────────────────────────────
def parse_docx(path: str):
    """Returns a list of { number, title, slug, sets, quizzes } modules."""
    doc = Document(path)
    modules = []
    current_module = None
    current_set = None
    current_quiz = None
    card_counter = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        # Module header
        m = re.match(r'^Module (\d+) – (.+)$', text)
        if m:
            current_module = {
                'number': int(m.group(1)),
                'title': m.group(2).strip(),
                'slug': slugify(m.group(2)),
                'sets': [],
                'quizzes': [],
            }
            modules.append(current_module)
            current_set = None
            current_quiz = None
            card_counter = 0
            continue

        # Track header — skip
        if re.match(r'^TRACK \d+ —', text):
            continue

        # Flashcard Set
        m = re.match(r'^Flashcard Set ([ABC])$', text)
        if m and current_module:
            current_set = {'letter': m.group(1), 'cards': []}
            current_module['sets'].append(current_set)
            current_quiz = None
            card_counter = 0
            continue

        # Micro-quiz header
        m = re.match(r'^Micro-Quiz (\d+) \(3 questions\)$', text)
        if m and current_module:
            current_quiz = {'number': int(m.group(1)), 'questions': []}
            current_module['quizzes'].append(current_quiz)
            current_set = None
            continue

        # Question: "Prompt → Answer" (number may or may not be in run text)
        if current_quiz and ' → ' in text and not text.startswith('Micro-Quiz'):
            m = re.match(r'^(.+?)\s+→\s+(.+)$', text)
            if m:
                prompt, answer = m.group(1).strip(), m.group(2).strip()
                if answer.lower() in ('true', 'false'):
                    kind = 'truefalse'
                    options = ['True', 'False']
                    correct = {'answer': answer.lower() == 'true'}
                else:
                    kind = 'mcq'
                    options = [answer]
                    correct = {'answer': 0}
                current_quiz['questions'].append({
                    'number': len(current_quiz['questions']) + 1,
                    'prompt': prompt,
                    'kind': kind,
                    'options': options,
                    'correct': correct,
                    'explanation': '',
                })
                continue

        # Card: 2 runs, run 0 = term, run 1+ = body
        if not current_set:
            continue
        runs = [r.text for r in para.runs if r.text]
        if not runs:
            continue
        first_run = runs[0].strip()
        if not first_run:
            continue
        card_counter += 1
        current_set['cards'].append({
            'number': card_counter,
            'term': first_run,
            'back': ' '.join(r.strip() for r in runs[1:] if r.strip()),
        })

    return modules


# ────────────────────────────────────────────────────────────────────
# SQL EMITTERS — adapt these to your schema
# ────────────────────────────────────────────────────────────────────
def emit_set(module, set_obj):
    """Generate SQL to create a lesson + its flashcard sections."""
    cards = set_obj['cards']
    if not cards:
        return ''
    out = []
    out.append(f"-- Set {set_obj['letter']}: cards {cards[0]['number']}-{cards[-1]['number']}")
    out.append(
        f"INSERT INTO public.education_lessons "
        f"(module_id, slug, title, summary, est_minutes, order_idx)"
    )
    out.append(
        f"SELECT m.id, %s, %s, %s, 3, %d" % (
            repr(set_obj['slug']),
            repr(f"{module['title']} — Set {set_obj['letter']}"),
            repr(f"Cards {cards[0]['number']}-{cards[-1]['number']}"),
            ord(set_obj['letter']) - ord('A') + 1,
        )
    )
    out.append(f"FROM public.education_modules m WHERE m.slug = %s;" % repr(module['slug']))

    for idx, card in enumerate(cards, 1):
        term_esc = card['term'].replace("'", "''")
        back_esc = card['back'].replace("'", "''")
        out.append(
            "INSERT INTO public.education_lesson_sections "
            "(lesson_id, order_idx, kind, title, body_md, flashcard_term, flashcard_back_md)"
        )
        out.append(
            f"SELECT l.id, {idx}, 'flashcard', '{term_esc}', "
            f"'**{term_esc}** — {back_esc}', '{term_esc}', '{back_esc}'"
        )
        out.append(
            f"FROM public.education_lessons l "
            f"JOIN public.education_modules m ON m.id = l.module_id"
        )
        out.append(
            f"WHERE m.slug = %s AND l.slug = %s;" % (repr(module['slug']), repr(set_obj['slug']))
        )
    return '\n'.join(out)


def emit_quiz(module, set_letter, quiz, lesson_slug):
    """Generate SQL for a micro-quiz + its questions."""
    out = []
    quiz_title = f"{module['title']} — Micro-Quiz {quiz['number']}"
    out.append(
        f"INSERT INTO public.education_quizzes "
        f"(scope, module_id, title, description, pass_pct, points)"
    )
    out.append(
        f"SELECT 'lesson', m.id, %s, %s, 70, 0" % (
            repr(quiz_title), repr(f"Set {set_letter} review"),
        )
    )
    out.append(f"FROM public.education_modules m WHERE m.slug = %s;" % repr(module['slug']))

    for q_idx, q in enumerate(quiz['questions'], 1):
        prompt_esc = q['prompt'].replace("'", "''")
        options_json = '[' + ','.join(repr(o) for o in q['options']) + ']'
        if q['kind'] == 'truefalse':
            correct_json = '{"answer": ' + str(q['correct']['answer']).lower() + '}'
        else:
            correct_json = '{"answer": 0}'
        out.append(
            "INSERT INTO public.education_quiz_questions "
            "(quiz_id, order_idx, kind, prompt_md, options, correct, explanation_md, points)"
        )
        out.append(
            f"SELECT q.id, {q_idx}, '{q['kind']}', "
            f"%s, %s::jsonb, %s::jsonb, '', 0" % (
                repr(prompt_esc), repr(options_json), repr(correct_json),
            )
        )
        out.append(
            f"FROM public.education_quizzes q "
            f"JOIN public.education_modules m ON m.id = q.module_id"
        )
        out.append(
            f"WHERE m.slug = %s AND q.title = %s;" % (repr(module['slug']), repr(quiz_title))
        )

    out.append("UPDATE public.education_lessons")
    out.append("SET micro_quiz_id = (")
    out.append("    SELECT q.id FROM public.education_quizzes q")
    out.append("    JOIN public.education_modules m ON m.id = q.module_id")
    out.append(
        f"    WHERE m.slug = %s AND q.title = %s AND q.scope = 'lesson'" % (
            repr(module['slug']), repr(quiz_title),
        )
    )
    out.append("    LIMIT 1")
    out.append(")")
    out.append(f"WHERE slug = %s;" % repr(lesson_slug))
    return '\n'.join(out)


# ────────────────────────────────────────────────────────────────────
# MAIN
# ────────────────────────────────────────────────────────────────────
def main():
    modules = parse_docx(DOC_PATH)
    out = [
        "-- Generated by docx-to-sql-education.py",
        "--",
        f"-- Source: {DOC_PATH}",
        f"-- Modules: {len(modules)}",
        "",
    ]
    for module in modules:
        if not module['sets']:
            continue
        # Build the slug prefix for THIS module. Modules reset their
        # counter per track in the doc ("Module 1", "Module 2", ...), but
        # our SQL needs globally-unique slugs. Use a per-module slug based
        # on the module's own slug (which is globally unique).
        mod_slug_prefix = module['slug'][:24]
        for set_obj in module['sets']:
            set_obj['slug'] = f"{mod_slug_prefix}-set-{set_obj['letter'].lower()}"
        out.append(f"\n-- {'=' * 70}")
        out.append(f"-- Module {module['number']}: {module['title']}")
        out.append(f"-- {'=' * 70}\n")
        set_letters = [s['letter'] for s in module['sets']]
        for set_obj in module['sets']:
            out.append(emit_set(module, set_obj))
        for i, quiz in enumerate(module['quizzes']):
            set_letter = set_letters[i] if i < len(set_letters) else set_letters[i % len(set_letters)]
            lesson_slug = f"{mod_slug_prefix}-set-{set_letter.lower()}"
            out.append(emit_quiz(module, set_letter, quiz, lesson_slug))

    print('\n'.join(out))


if __name__ == '__main__':
    main()
