#!/usr/bin/env python3
"""multi-turn-eval 3편(MultiChallenge)의 그림 두 장을 SVG 로 그린다. 두 언어 트리에 같은 파일을 쓴다.

논문은 arXiv 기본 라이선스라 그림을 실을 수 없다. 4.1 · 4.2절의 글과 저자
저장소(ekwinox117/multi-challenge)의 src/evaluator.py 를 보고 새로 그렸다.

    mc-pipeline.svg   문제를 만드는 과정 (MMSE + 사람 검수)
    mc-eval.svg       채점하는 과정

    python3 scripts/gen_multichallenge_graphs.py
"""
import os
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTS = [os.path.join(ROOT, lang, "src", "multi-turn-eval") for lang in ("ko", "en")]

FONT = "ui-monospace,Menlo,monospace"
PAL = {
    "raw":  ("#f2f3f5", "#5b6572"),   # 입력 · 데이터
    "llm":  ("#fdf1e6", "#b5733a"),   # LLM
    "note": ("#e9f1fb", "#3b6ea5"),   # 사람
    "out":  ("#edf5ec", "#4a7c4e"),   # 결과
    "bad":  ("#fbecec", "#a54a4a"),   # 버림
}
LINE, LABEL, INK, MUTE = "#9aa3b0", "#6b7280", "#1f2430", "#6b7280"
BAND, BAND_EDGE = "#fafbfc", "#e5e8ec"


def svg(name, w, h, parts):
    body = "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}">',
        '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>',
        f'<rect width="{w}" height="{h}" fill="#fff"/>',
        *parts,
        '</svg>'])
    for d in OUTS:
        open(os.path.join(d, name), "w").write(body)
    print("wrote", name)


def text(p, x, y, s, size=11, fill=INK, anchor="start", weight=None):
    wt = f' font-weight="{weight}"' if weight else ""
    p.append(f'<text x="{x:.0f}" y="{y:.0f}" font-size="{size}" fill="{fill}" '
             f'text-anchor="{anchor}"{wt}>{escape(s)}</text>')


def box(p, x, y, w, h, label, kind, subs=(), bold=False):
    fill, stroke = PAL[kind]
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
             f'fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
    cx = x + w / 2
    top = y + h / 2 - 7 * len(subs) + 4
    text(p, cx, top, label, 12.5, anchor="middle",
         weight="bold" if bold else None)
    for i, s in enumerate(subs):
        text(p, cx, top + 16 + i * 14, s, 10, MUTE, "middle")


def band(p, x, y, w, h, title):
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" '
             f'fill="{BAND}" stroke="{BAND_EDGE}" stroke-width="1"/>')
    text(p, x + 16, y + 20, title, 11, MUTE)


def line(p, x1, y1, x2, y2, label=None, dx=0, dy=-7, anchor="middle"):
    p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{LINE}" '
             f'stroke-width="1.4" marker-end="url(#a)"/>')
    if label:
        text(p, (x1 + x2) / 2 + dx, (y1 + y2) / 2 + dy, label, 10, LABEL, anchor)


def path(p, d, label=None, lx=0, ly=0, anchor="middle"):
    p.append(f'<path d="{d}" fill="none" stroke="{LINE}" stroke-width="1.4" '
             'marker-end="url(#a)"/>')
    if label:
        text(p, lx, ly, label, 10, LABEL, anchor)


# ------------------------------------------------------------ 만드는 과정
def pipeline():
    p = []
    W, H = 760, 470

    # 입력 셋 — 셋 다 Planner 로 들어간다
    band(p, 12, 12, 736, 86, "INPUT")
    box(p, 30, 40, 210, 46, "topic seed", "raw", ("knowledge domains",))
    box(p, 275, 40, 210, 46, "persona seed", "raw", ("PersonaHub",))
    box(p, 520, 40, 210, 46, "category config", "raw", ("pass / fail rules",))
    band(p, 12, 118, 736, 190, "MMSE")
    for x in (135, 380, 625):
        p.append(f'<line x1="{x}" y1="86" x2="{x}" y2="106" stroke="{LINE}" '
                 'stroke-width="1.4"/>')
    p.append(f'<line x1="135" y1="106" x2="625" y2="106" stroke="{LINE}" '
             'stroke-width="1.4"/>')
    line(p, 135, 106, 135, 146)

    # 대화를 만드는 loop
    box(p, 30, 150, 200, 60, "Planner", "llm", ("writes the blueprint",
                                                "checks for a failure"))
    box(p, 290, 150, 180, 60, "User agent", "llm", ("turns the blueprint",
                                                    "into a user turn"))
    box(p, 530, 150, 200, 60, "Responder", "llm", ("one of 6 frontier models",
                                                   "picked at random"))
    line(p, 230, 172, 286, 172, "blueprint")
    line(p, 470, 172, 526, 172, "user turn")
    path(p, "M630,210 V244 H130 V214", "reply", 380, 238)
    text(p, 220, 284, "repeat until a failure or the turn limit", 10.5, MUTE)
    box(p, 560, 256, 170, 40, "turn limit hit", "bad", ("discard",))

    # 사람 검수
    band(p, 12, 322, 736, 136, "HUMAN")
    box(p, 30, 360, 230, 74, "annotator edits", "note",
        ("fits the category?", "natural?", "≥ 3 of 6 models fail?"))
    box(p, 300, 360, 180, 74, "2 review layers", "note",
        ("a different", "reviewer pool"))
    box(p, 520, 360, 210, 74, "test example", "out",
        ("conversation + one", "yes / no question"), bold=True)
    line(p, 100, 210, 100, 356, "failure found", dx=8, dy=0, anchor="start")
    line(p, 260, 397, 296, 397)
    line(p, 480, 397, 516, 397)
    svg("mc-pipeline.svg", W, H, p)


# ------------------------------------------------------------ 채점하는 과정
def evaluation():
    p = []
    W, H = 760, 300

    box(p, 16, 30, 190, 96, "CONVERSATION", "raw",
        ("user · assistant · ...", "ends with a user turn", "about 9 turns"))
    box(p, 256, 46, 150, 64, "your model", "out", ("writes one reply",),
        bold=True)
    box(p, 456, 46, 150, 64, "reply", "raw", ("only this goes", "to the judge"))
    line(p, 206, 78, 252, 78)
    line(p, 406, 78, 452, 78)

    box(p, 16, 176, 190, 74, "TARGET_QUESTION", "raw",
        ("one yes / no question", "written by a person"))
    box(p, 456, 176, 150, 74, "judge", "llm", ("gpt-4o-2024-08-06",
                                               "temperature 0"))
    line(p, 531, 110, 531, 172)
    line(p, 206, 213, 452, 213, "\"Be VERY STRICT!\"")
    box(p, 640, 176, 104, 74, "pass?", "out", ("verdict ==", "PASS_CRITERIA"),
        bold=True)
    line(p, 606, 213, 636, 213)

    text(p, 16, 282, "the judge never sees the conversation — "
         "only the reply and the question", 10.5, MUTE)
    svg("mc-eval.svg", W, H, p)


pipeline()
evaluation()
