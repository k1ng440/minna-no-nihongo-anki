"""Shared CSS + vocab/quiz card HTML templates."""

CSS = """.card { font-family: "Noto Sans CJK JP","Hiragino Sans",sans-serif; font-size: 24px; text-align: center; padding: 16px; }
.theme-bar { height: 6px; border-radius: 3px; margin-bottom: 14px; opacity: 0.9; }
.jp { font-size: 54px; margin: 12px 0; font-weight: 600; }
.kana { font-size: 28px; opacity: 0.85; margin: 6px 0; }
.pitch { display: inline-block; letter-spacing: 0.04em; }
.pitch .hi, .pitch .lo, .pitch .drop { display: inline-block; padding: 2px 1px 0; line-height: 1.1; }
.pitch .hi { border-top: 3px solid #e74c3c; }
.pitch .lo { border-top: 3px solid transparent; }
.pitch .drop { border-right: 3px solid #e74c3c; padding-right: 3px; }
.meaning { font-size: 22px; color: #2ecc71; margin: 10px 0; font-weight: 500; }
.meaning-bn { font-size: 20px; color: #f39c12; margin: 4px 0 10px; font-weight: 500; }
.sentence-jp { font-size: 22px; margin: 14px 0 4px; }
.sentence-en { font-size: 16px; opacity: 0.7; margin-bottom: 4px; font-style: italic; }
.sentence-bn { font-size: 16px; opacity: 0.7; margin-bottom: 8px; }
.mnemonic { font-style: italic; color: #b89cef; background: rgba(160,120,220,0.15); padding: 10px 14px; border-radius: 10px; margin: 12px auto; max-width: 90%; font-size: 17px; text-align: left; }
.mnemonic::before { content: "🧠 "; }
.mnemonic-bn { color: #e67e22; background: rgba(230,126,34,0.12); padding: 10px 14px; border-radius: 10px; margin: 8px auto; max-width: 90%; font-size: 16px; text-align: left; }
.mnemonic-bn::before { content: "🧠 "; }
.kanji-svg svg { width: 140px; height: 140px; stroke: currentColor; }
.kanji-svg svg path { stroke: currentColor !important; }
.kanji-svgs { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
.mascot { float: right; opacity: 0.85; }
.mascot svg { width: 70px; height: 70px; }
.footer { clear: both; display: flex; align-items: center; justify-content: space-between; margin-top: 14px; padding-top: 10px; border-top: 1px solid currentColor; opacity: 0.7; font-size: 13px; }
.prog { flex: 1; background: rgba(128,128,128,0.25); height: 6px; border-radius: 3px; overflow: hidden; margin: 0 12px; }
.prog-fill { height: 100%; transition: width 0.6s; }
.lesson-emoji { font-size: 18px; }
hr#answer { border: 0; border-top: 2px dashed currentColor; opacity: 0.4; margin: 16px 0; }
.cloze-blank { background: #ffd166; padding: 0 8px; border-radius: 4px; color: transparent; }
.quiz-prompt { font-size: 42px; margin: 18px 0 24px; font-weight: 600; }
.choices { display: flex; flex-direction: column; gap: 8px; max-width: 360px; margin: 0 auto; }
.choice { padding: 12px 16px; border: 2px solid rgba(128,128,128,0.4); border-radius: 10px; font-size: 20px; text-align: left; }
.choice .letter { font-weight: bold; margin-right: 8px; opacity: 0.6; }
.correct-c1 .c1, .correct-c2 .c2, .correct-c3 .c3, .correct-c4 .c4 { background: rgba(46,204,113,0.25); border-color: #2ecc71; }
.correct-c1 .c1 .letter, .correct-c2 .c2 .letter, .correct-c3 .c3 .letter, .correct-c4 .c4 .letter { color: #2ecc71; opacity: 1; }
"""

VOCAB_TEMPLATES = [
    {
        "name": "JP -> EN",
        "qfmt": """<div class="theme-bar" style="background:{{LessonTheme}}"></div>
{{#Kanji}}<div class="jp">{{Kanji}}</div><div class="kana">{{KanaPitch}}</div>{{/Kanji}}{{^Kanji}}<div class="jp">{{Kana}}</div>{{/Kanji}}""",
        "afmt": """{{FrontSide}}<hr id="answer">
<div class="meaning">{{Meaning}}</div>
{{#MeaningBn}}<div class="meaning-bn">{{MeaningBn}}</div>{{/MeaningBn}}
<div class="audio">{{Audio}}</div>
{{#KanjiSVG}}<div class="kanji-svgs">{{KanjiSVG}}</div>{{/KanjiSVG}}
{{#Image}}<div class="image">{{Image}}</div>{{/Image}}
{{#SentenceJP}}<div class="sentence-jp">{{SentenceJP}} {{SentenceAudio}}</div>
<div class="sentence-en">{{SentenceEN}}</div>
{{#SentenceBn}}<div class="sentence-bn">{{SentenceBn}}</div>{{/SentenceBn}}{{/SentenceJP}}
{{#Mnemonic}}<div class="mnemonic">{{Mnemonic}}</div>{{/Mnemonic}}
{{#MnemonicBn}}<div class="mnemonic-bn">{{MnemonicBn}}</div>{{/MnemonicBn}}
<div class="footer">
  <div class="lesson-emoji">{{LessonEmoji}}</div>
  {{ProgressBar}}
  <div class="mascot">{{Mascot}}</div>
</div>""",
    },
    {
        "name": "EN -> JP",
        "qfmt": """<div class="theme-bar" style="background:{{LessonTheme}}"></div>
<div class="meaning" style="font-size:36px;color:#222">{{Meaning}}</div>""",
        "afmt": """{{FrontSide}}<hr id="answer">
{{#Kanji}}<div class="jp">{{Kanji}}</div><div class="kana">{{KanaPitch}}</div>{{/Kanji}}{{^Kanji}}<div class="jp">{{Kana}}</div>{{/Kanji}}
<div class="audio">{{Audio}}</div>
{{#KanjiSVG}}<div class="kanji-svgs">{{KanjiSVG}}</div>{{/KanjiSVG}}
{{#SentenceJP}}<div class="sentence-jp">{{SentenceJP}} {{SentenceAudio}}</div>
<div class="sentence-en">{{SentenceEN}}</div>
{{#SentenceBn}}<div class="sentence-bn">{{SentenceBn}}</div>{{/SentenceBn}}{{/SentenceJP}}
{{#Mnemonic}}<div class="mnemonic">{{Mnemonic}}</div>{{/Mnemonic}}
{{#MnemonicBn}}<div class="mnemonic-bn">{{MnemonicBn}}</div>{{/MnemonicBn}}
<div class="footer"><div class="lesson-emoji">{{LessonEmoji}}</div>{{ProgressBar}}<div class="mascot">{{Mascot}}</div></div>""",
    },
    {
        "name": "Audio -> JP+EN",
        "qfmt": """<div class="theme-bar" style="background:{{LessonTheme}}"></div>
<div class="audio" style="font-size:60px">🔊 {{Audio}}</div>""",
        "afmt": """{{FrontSide}}<hr id="answer">
{{#Kanji}}<div class="jp">{{Kanji}}</div><div class="kana">{{KanaPitch}}</div>{{/Kanji}}{{^Kanji}}<div class="jp">{{Kana}}</div>{{/Kanji}}
<div class="meaning">{{Meaning}}</div>
{{#MeaningBn}}<div class="meaning-bn">{{MeaningBn}}</div>{{/MeaningBn}}
{{#Image}}<div class="image">{{Image}}</div>{{/Image}}
<div class="footer"><div class="lesson-emoji">{{LessonEmoji}}</div>{{ProgressBar}}<div class="mascot">{{Mascot}}</div></div>""",
    },
    {
        "name": "Sentence Cloze",
        "qfmt": """{{#SentenceCloze}}<div class="theme-bar" style="background:{{LessonTheme}}"></div>
<div class="sentence-jp" style="font-size:30px">{{SentenceCloze}}</div>
<div class="sentence-en">{{SentenceEN}}</div>{{/SentenceCloze}}""",
        "afmt": """{{#SentenceCloze}}{{FrontSide}}<hr id="answer">
<div class="sentence-jp" style="font-size:30px">{{SentenceJP}} {{SentenceAudio}}</div>
{{#Kanji}}<div class="jp" style="font-size:36px">{{Kanji}}</div>{{/Kanji}}
<div class="kana">{{KanaPitch}}</div>
<div class="meaning">{{Meaning}}</div>
{{#MeaningBn}}<div class="meaning-bn">{{MeaningBn}}</div>{{/MeaningBn}}
<div class="footer"><div class="lesson-emoji">{{LessonEmoji}}</div>{{ProgressBar}}<div class="mascot">{{Mascot}}</div></div>{{/SentenceCloze}}""",
    },
    {
        "name": "Kanji Stroke",
        "qfmt": """{{#KanjiSVG}}<div class="theme-bar" style="background:{{LessonTheme}}"></div>
<div class="kanji-svgs" style="margin:20px 0">{{KanjiSVG}}</div>{{/KanjiSVG}}""",
        "afmt": """{{#KanjiSVG}}{{FrontSide}}<hr id="answer">
<div class="jp">{{Kanji}}</div>
<div class="kana">{{KanaPitch}}</div>
<div class="meaning">{{Meaning}}</div>
{{#MeaningBn}}<div class="meaning-bn">{{MeaningBn}}</div>{{/MeaningBn}}
<div class="audio">{{Audio}}</div>
<div class="footer"><div class="lesson-emoji">{{LessonEmoji}}</div>{{ProgressBar}}<div class="mascot">{{Mascot}}</div></div>{{/KanjiSVG}}""",
    },
]

QUIZ_TEMPLATE = {
    "name": "Quiz",
    "qfmt": """<div class="theme-bar" style="background:{{LessonTheme}}"></div>
<div class="quiz-prompt">{{Prompt}}</div>
<div class="choices">
  <div class="choice c1"><span class="letter">A.</span>{{Choice1}}</div>
  <div class="choice c2"><span class="letter">B.</span>{{Choice2}}</div>
  <div class="choice c3"><span class="letter">C.</span>{{Choice3}}</div>
  <div class="choice c4"><span class="letter">D.</span>{{Choice4}}</div>
</div>""",
    "afmt": """<div class="theme-bar" style="background:{{LessonTheme}}"></div>
<div class="quiz-prompt">{{Prompt}}</div>
<div class="choices {{CorrectClass}}">
  <div class="choice c1"><span class="letter">A.</span>{{Choice1}}</div>
  <div class="choice c2"><span class="letter">B.</span>{{Choice2}}</div>
  <div class="choice c3"><span class="letter">C.</span>{{Choice3}}</div>
  <div class="choice c4"><span class="letter">D.</span>{{Choice4}}</div>
</div>""",
}

INFO_CSS = """
.card { text-align: left !important; font-family: "Noto Sans CJK JP","Hiragino Sans",sans-serif; }
.info-card { text-align: left; max-width: 640px; margin: 0 auto; padding: 12px; line-height: 1.4; font-size: 16px; }
.info-card * { text-align: inherit; }
.info-card img.info-cover { display: block; max-width: 200px; width: 100%; margin: 0 auto 8px; border-radius: 6px; box-shadow: 0 3px 10px rgba(0,0,0,0.25); }
.info-card h1 { font-size: 26px; margin: 4px 0 2px; text-align: center; font-weight: 700; line-height: 1.15; }
.info-card h2 { font-size: 17px; margin: 14px 0 4px; border-bottom: 1px solid currentColor; padding-bottom: 2px; font-weight: 600; opacity: 0.95; }
.info-card .subtitle { text-align: center; opacity: 0.7; margin: 0 0 10px; font-style: italic; font-size: 14px; }
.info-card p { margin: 4px 0; }
.info-card ul { padding-left: 20px; margin: 4px 0; }
.info-card li { margin: 2px 0; }
.info-card code { background: rgba(128,128,128,0.22); padding: 0 5px; border-radius: 3px; font-size: 14px; font-family: monospace; }
.info-card a { color: #4a9eff; text-decoration: none; }
.info-card .author { text-align: center; margin: 14px 0 4px; padding: 10px; border: 1px solid rgba(128,128,128,0.4); border-radius: 8px; }
.info-card .author .name { font-size: 18px; font-weight: 600; margin-bottom: 3px; }
.info-card .tip { background: rgba(255,200,80,0.15); border-left: 3px solid #ffc850; padding: 6px 10px; border-radius: 5px; margin: 8px 0; font-size: 15px; }
"""

INFO_TEMPLATE = {
    "name": "Info",
    "qfmt": '<div class="info-card">{{Body}}</div>',
    "afmt": '<div class="info-card">{{Body}}</div>',
}
