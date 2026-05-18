"""genanki Models — IDs stable across runs to preserve Anki review history."""
import genanki

from mnn.deck.templates import (
    CSS,
    INFO_CSS,
    INFO_TEMPLATE,
    QUIZ_TEMPLATE,
    VOCAB_TEMPLATES,
)

VOCAB_MODEL = genanki.Model(
    1607392320,
    "Minna no Nihongo Vocab",
    fields=[
        {"name": "Kanji"}, {"name": "Kana"}, {"name": "Meaning"},
        {"name": "Audio"}, {"name": "Lesson"},
        {"name": "KanaPitch"}, {"name": "SentenceJP"}, {"name": "SentenceEN"},
        {"name": "SentenceAudio"}, {"name": "SentenceCloze"},
        {"name": "KanjiSVG"}, {"name": "Mnemonic"}, {"name": "Image"},
        {"name": "Mascot"}, {"name": "LessonTheme"}, {"name": "LessonEmoji"},
        {"name": "ProgressBar"},
    ],
    templates=VOCAB_TEMPLATES,
    css=CSS,
)

QUIZ_MODEL = genanki.Model(
    1607392321,
    "Minna no Nihongo Quiz",
    fields=[
        {"name": "Prompt"}, {"name": "Choice1"}, {"name": "Choice2"},
        {"name": "Choice3"}, {"name": "Choice4"}, {"name": "CorrectClass"},
        {"name": "Lesson"}, {"name": "Direction"}, {"name": "LessonTheme"},
    ],
    templates=[QUIZ_TEMPLATE],
    css=CSS,
)

INFO_MODEL = genanki.Model(
    1607392322,
    "Minna no Nihongo Info",
    fields=[{"name": "Title"}, {"name": "Body"}],
    templates=[INFO_TEMPLATE],
    css=INFO_CSS,
)
