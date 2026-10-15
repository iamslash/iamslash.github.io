#!/usr/bin/env python3
"""multi-turn-eval 시리즈의 차트와 그림을 SVG 로 그린다. 두 언어 트리에 같은 파일을 쓴다.

숫자는 전부 논문 원문에서 옮겼다. 색은 dataviz 기본 팔레트의 앞 세 칸
(파랑 · 주황 · 청록)만 쓰고, 청록은 대비가 낮아 값을 막대 옆에 직접 적는다.

    mt-timeline.svg     02  방법들의 연대표 (써 둔 대화 / LLM 사용자)
    mc-results.svg      03  MultiChallenge 사람 채점 평균 (Table 2)
    mc-judge.svg        03  판정 방식별 사람과의 일치율 (Table 4)
    tau2-dual.svg       04  τ2-Bench 의 구조 (agent tool · user tool · 같은 세계)
    tau2-passk.svg      04  gpt-4.1 의 pass^k (Figure 3)
    tau2-ablation.svg   04  기본 · 사용자 없음 · 정답 계획 (Figure 4 왼쪽)
    ts-userprompt.svg   05  사용자 프롬프트 구성별 시뮬레이터 오류 (ToolSandbox Table 2)
    eval-single.svg     06  써 둔 대화로 재는 절차
    eval-multi.svg      06  LLM 사용자로 재는 절차

    python3 scripts/gen_multiturn_charts.py
"""
import os
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTS = [os.path.join(ROOT, lang, "src", "multi-turn-eval") for lang in ("ko", "en")]

FONT = "ui-monospace,Menlo,monospace"
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"     # 범주색 1 · 2 · 3
INK, INK2, MUTE = "#0b0b0b", "#52514e", "#8a8984"
GRID, AXIS, SURF = "#e8e7e3", "#c9c8c3", "#ffffff"
PAL = {                                           # 도식용 (기존 그림과 같은 톤)
    "raw":  ("#f2f3f5", "#5b6572"),
    "llm":  ("#fdf1e6", "#b5733a"),
    "note": ("#e9f1fb", "#3b6ea5"),
    "out":  ("#edf5ec", "#4a7c4e"),
}
LINE = "#9aa3b0"


def svg(name, w, h, parts):
    body = "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT}">',
        '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{LINE}"/></marker></defs>',
        f'<rect width="{w}" height="{h}" fill="{SURF}"/>',
        *parts, '</svg>'])
    for d in OUTS:
        open(os.path.join(d, name), "w").write(body)
    print("wrote", name)


def t(p, x, y, s, size=11, fill=INK, anchor="start", weight=None):
    wt = f' font-weight="{weight}"' if weight else ""
    p.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
             f'text-anchor="{anchor}"{wt}>{escape(s)}</text>')


def ln(p, x1, y1, x2, y2, color=GRID, wdt=1, arrow=False, dash=None):
    m = ' marker-end="url(#a)"' if arrow else ""
    d = f' stroke-dasharray="{dash}"' if dash else ""
    p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
             f'stroke="{color}" stroke-width="{wdt}"{m}{d}/>')


def bar(p, x, y, w, h, color):
    """막대. 바깥 끝만 4px 둥글게 하고, 기준선 쪽은 각지게 둔다."""
    r = min(4, h / 2, w / 2)
    p.append(f'<path d="M{x:.1f},{y:.1f} H{x + w - r:.1f} '
             f'Q{x + w:.1f},{y:.1f} {x + w:.1f},{y + r:.1f} V{y + h - r:.1f} '
             f'Q{x + w:.1f},{y + h:.1f} {x + w - r:.1f},{y + h:.1f} H{x:.1f} Z" '
             f'fill="{color}"/>')


def vbar(p, x, y0, w, h, color):
    """세로 막대. 위쪽 끝만 둥글게."""
    r = min(4, w / 2, h / 2) if h > 0 else 0
    top = y0 - h
    p.append(f'<path d="M{x:.1f},{y0:.1f} V{top + r:.1f} '
             f'Q{x:.1f},{top:.1f} {x + r:.1f},{top:.1f} H{x + w - r:.1f} '
             f'Q{x + w:.1f},{top:.1f} {x + w:.1f},{top + r:.1f} V{y0:.1f} Z" '
             f'fill="{color}"/>')


def legend(p, x, y, items):
    for i, (label, color) in enumerate(items):
        xx = x + i * 170
        p.append(f'<rect x="{xx}" y="{y - 9}" width="10" height="10" rx="2" '
                 f'fill="{color}"/>')
        t(p, xx + 16, y, label, 11, INK2)


def box(p, x, y, w, h, label, kind, subs=(), bold=False):
    fill, stroke = PAL[kind]
    p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
             f'fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
    cx = x + w / 2
    top = y + h / 2 - 7 * len(subs) + 4
    t(p, cx, top, label, 12.5, INK, "middle", "bold" if bold else None)
    for i, s in enumerate(subs):
        t(p, cx, top + 16 + i * 14, s, 10, "#6b7280", "middle")


# ---------------------------------------------------------------- 02 연대표
def timeline():
    p = []
    W, H = 760, 350
    x0, x1 = 140, 730                     # 2023-06 … 2025-08
    def X(y, m): return x0 + ((y - 2023) * 12 + (m - 6)) / 26 * (x1 - x0)
    lanes = {"one": 120, "many": 240}
    t(p, 16, 26, "multi-turn evaluation methods, by arXiv month", 12.5, INK,
      weight="bold")
    for y, m, lab in [(2023, 6, "2023-06"), (2024, 1, "2024-01"),
                      (2024, 7, "2024-07"), (2025, 1, "2025-01"),
                      (2025, 7, "2025-07")]:
        ln(p, X(y, m), 60, X(y, m), 305, GRID)
        t(p, X(y, m), 326, lab, 10, MUTE, "middle")
    for key, lab, sub in [("one", "scripted", "user turns fixed"),
                          ("many", "LLM user", "sees replies")]:
        yy = lanes[key]
        ln(p, x0, yy, x1, yy, AXIS)
        t(p, 16, yy - 2, lab, 11, INK, weight="bold")
        t(p, 16, yy + 12, sub, 10, MUTE)
    items = [  # (y, m, lane, name, label-offset)
        (2023, 6, "one", "MT-Bench", -16),
        (2024, 2, "one", "MT-Bench-101", -16),
        (2025, 1, "one", "MultiChallenge", -16),
        (2023, 9, "many", "MINT", -16),
        (2023, 10, "many", "SOTOPIA", 24),
        (2024, 6, "many", "τ-bench", -16),
        (2024, 8, "many", "ToolSandbox", 24),
        (2025, 1, "many", "ACEBench (Agent)", -16),
        (2025, 1, "many", "IntellAgent", 24),
        (2025, 3, "many", "ColBench", 40),
        (2025, 5, "many", "Lost in Conv.", -40),
        (2025, 6, "many", "τ2-Bench", -16),
        (2025, 7, "many", "UserBench", 24),
    ]
    for y, m, lane, name, off in items:
        cx, cy = X(y, m), lanes[lane]
        color = S1 if lane == "one" else S2
        p.append(f'<circle cx="{cx:.1f}" cy="{cy}" r="5" fill="{color}" '
                 f'stroke="{SURF}" stroke-width="2"/>')
        if abs(off) > 16:
            ln(p, cx, cy + (6 if off > 0 else -6), cx, cy + off - (10 if off > 0 else -4),
               AXIS)
        t(p, cx, cy + off + (0 if off < 0 else 4), name, 10.5, INK2, "middle")
    svg("mt-timeline.svg", W, H, p)


# --------------------------------------------------------- 03 MultiChallenge
def mc_results():
    p = []
    rows = [("Claude 3.5 Sonnet (Jun)", 41.42), ("o1-preview", 37.23),
            ("Gemini 1.5 Pro", 19.96), ("Llama 3.1 405B", 14.92),
            ("Mistral Large", 14.63), ("GPT-4o (Aug)", 12.52)]
    W, H = 720, 60 + len(rows) * 34 + 30
    x0, x1 = 210, 640
    t(p, 16, 26, "MultiChallenge — average accuracy, human-graded (%)", 12.5,
      INK, weight="bold")
    for v in (0, 25, 50):
        x = x0 + v / 60 * (x1 - x0)
        ln(p, x, 44, x, H - 26, GRID)
        t(p, x, H - 10, str(v), 10, MUTE, "middle")
    for i, (name, v) in enumerate(rows):
        y = 52 + i * 34
        t(p, x0 - 10, y + 15, name, 11, INK2, "end")
        bar(p, x0, y + 3, v / 60 * (x1 - x0), 18, S1)
        t(p, x0 + v / 60 * (x1 - x0) + 6, y + 16, f"{v:.1f}", 11, INK)
    ln(p, x0, 44, x0, H - 26, AXIS)
    svg("mc-results.svg", W, H, p)


def mc_judge():
    p = []
    cats = [("Instruction retention", 44.44, 92.26),
            ("Inference memory", 37.53, 94.62),
            ("Versioned editing", 31.82, 94.85),
            ("Self-coherence", 31.05, 94.12)]
    W, H = 720, 60 + len(cats) * 50 + 34
    x0, x1 = 200, 650
    t(p, 16, 26, "Agreement with human raters (%)", 12.5, INK, weight="bold")
    legend(p, 330, 26, [("judge reads the conversation", S2)])
    legend(p, 330, 44, [("judge reads one yes/no question", S1)])
    for v in (0, 50, 100):
        x = x0 + v / 100 * (x1 - x0)
        ln(p, x, 58, x, H - 26, GRID)
        t(p, x, H - 10, str(v), 10, MUTE, "middle")
    for i, (name, a, b) in enumerate(cats):
        y = 64 + i * 50
        t(p, x0 - 10, y + 20, name, 11, INK2, "end")
        bar(p, x0, y, a / 100 * (x1 - x0), 16, S2)
        t(p, x0 + a / 100 * (x1 - x0) + 6, y + 12, f"{a:.1f}", 10.5, INK)
        bar(p, x0, y + 18, b / 100 * (x1 - x0), 16, S1)
        t(p, x0 + b / 100 * (x1 - x0) + 6, y + 30, f"{b:.1f}", 10.5, INK)
    ln(p, x0, 58, x0, H - 26, AXIS)
    svg("mc-judge.svg", W, H, p)


# ------------------------------------------------------------- 04 τ2-Bench
def tau2_dual():
    p = []
    W, H = 760, 250
    box(p, 20, 30, 190, 70, "agent", "llm", ("reads the policy",
                                             "talks to the user"), bold=True)
    box(p, 550, 30, 190, 70, "user", "llm", ("an LLM playing a customer",
                                             "follows hidden instructions"),
        bold=True)
    ln(p, 214, 55, 546, 55, LINE, 1.4, True)
    ln(p, 546, 75, 214, 75, LINE, 1.4, True)
    t(p, 380, 49, "messages", 10, "#6b7280", "middle")
    box(p, 20, 150, 190, 70, "agent tools", "raw", ("e.g. look up a line,",
                                                    "turn on roaming"))
    box(p, 550, 150, 190, 70, "user tools", "raw", ("e.g. check status bar,",
                                                    "toggle airplane mode"))
    box(p, 285, 150, 190, 70, "shared world", "out", ("company DB + the phone",
                                                      "checked when it ends"),
        bold=True)
    ln(p, 115, 100, 115, 146, LINE, 1.4, True)
    ln(p, 645, 100, 645, 146, LINE, 1.4, True)
    ln(p, 210, 185, 281, 185, LINE, 1.4, True)
    ln(p, 550, 185, 479, 185, LINE, 1.4, True)
    svg("tau2-dual.svg", W, H, p)


def tau2_passk():
    p = []
    series = [("Retail", S1, [0.74, 0.64, 0.58, 0.53]),
              ("Airline", S2, [0.56, 0.46, 0.42, 0.40]),
              ("Telecom", S3, [0.34, 0.26, 0.22, 0.19])]
    W, H = 720, 320
    x0, x1, y0, y1 = 70, 560, 270, 60
    def X(k): return x0 + (k - 1) / 3 * (x1 - x0)
    def Y(v): return y0 - v / 0.8 * (y0 - y1)
    t(p, 16, 26, "gpt-4.1 on τ2-Bench — pass^k (all k runs must succeed)",
      12.5, INK, weight="bold")
    for v in (0, 0.2, 0.4, 0.6, 0.8):
        ln(p, x0, Y(v), x1, Y(v), GRID)
        t(p, x0 - 8, Y(v) + 4, f"{v:.1f}", 10, MUTE, "end")
    for k in (1, 2, 3, 4):
        t(p, X(k), y0 + 18, f"k = {k}", 10, MUTE, "middle")
    ln(p, x0, y0, x1, y0, AXIS)
    for name, color, vals in series:
        pts = " ".join(f"{X(k + 1):.1f},{Y(v):.1f}" for k, v in enumerate(vals))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{color}" '
                 'stroke-width="2"/>')
        for k, v in enumerate(vals):
            p.append(f'<circle cx="{X(k + 1):.1f}" cy="{Y(v):.1f}" r="4.5" '
                     f'fill="{color}" stroke="{SURF}" stroke-width="2"/>')
        t(p, X(1) - 10, Y(vals[0]) + 4, f"{vals[0]:.2f}", 10.5, INK, "end")
        t(p, X(4) + 10, Y(vals[3]) + 4, f"{vals[3]:.2f}  {name}", 10.5, INK)
    svg("tau2-passk.svg", W, H, p)


def tau2_ablation():
    p = []
    groups = ["default", "no user", "oracle plan"]
    data = [("gpt-4.1", S1, [0.34, 0.52, 0.73]),
            ("o4-mini", S2, [0.42, 0.67, 0.96])]
    W, H = 720, 300
    x0, x1, y0, y1 = 70, 680, 250, 60
    def Y(v): return y0 - v * (y0 - y1)
    t(p, 16, 26, "τ2-Bench telecom — pass^1 by mode", 12.5, INK, weight="bold")
    legend(p, 380, 26, [(n, c) for n, c, _ in data])
    for v in (0, 0.25, 0.5, 0.75, 1.0):
        ln(p, x0, Y(v), x1, Y(v), GRID)
        t(p, x0 - 8, Y(v) + 4, f"{v:.2f}", 10, MUTE, "end")
    gw = (x1 - x0) / 3
    for g, name in enumerate(groups):
        gx = x0 + g * gw
        t(p, gx + gw / 2, y0 + 18, name, 11, INK2, "middle")
        for s, (_, color, vals) in enumerate(data):
            bx = gx + gw / 2 - 46 + s * 48
            vbar(p, bx, y0, 44, vals[g] * (y0 - y1), color)
            t(p, bx + 22, Y(vals[g]) - 6, f"{vals[g]:.2f}", 10.5, INK, "middle")
    ln(p, x0, y0, x1, y0, AXIS)
    svg("tau2-ablation.svg", W, H, p)


# ------------------------------------------------------------- 05 프롬프트
def ts_userprompt():
    p = []
    rows = [("user goal only", 12.4, 6.20),
            ("+ knowledge boundary", 7.75, 3.88),
            ("+ demonstration", 6.97, 0.77)]
    W, H = 720, 60 + len(rows) * 50 + 34
    x0, x1 = 200, 650
    t(p, 16, 26, "ToolSandbox — user simulator errors (% of conversations)",
      12.5, INK, weight="bold")
    legend(p, 200, 46, [("hallucination", S2), ("instruction following", S1)])
    for v in (0, 5, 10, 15):
        x = x0 + v / 15 * (x1 - x0)
        ln(p, x, 58, x, H - 26, GRID)
        t(p, x, H - 10, str(v), 10, MUTE, "middle")
    for i, (name, a, b) in enumerate(rows):
        y = 64 + i * 50
        t(p, x0 - 10, y + 20, name, 11, INK2, "end")
        bar(p, x0, y, a / 15 * (x1 - x0), 16, S2)
        t(p, x0 + a / 15 * (x1 - x0) + 6, y + 12, f"{a:.2f}", 10.5, INK)
        bar(p, x0, y + 18, b / 15 * (x1 - x0), 16, S1)
        t(p, x0 + b / 15 * (x1 - x0) + 6, y + 30, f"{b:.2f}", 10.5, INK)
    ln(p, x0, 58, x0, H - 26, AXIS)
    svg("ts-userprompt.svg", W, H, p)


# ------------------------------------------------------------- 06 내 agent
def eval_single():
    p = []
    W, H = 760, 200
    box(p, 16, 30, 170, 80, "history", "raw", ("fixed turns,", "ends with a user turn"))
    box(p, 216, 30, 150, 80, "your agent", "out", ("one reply",), bold=True)
    box(p, 396, 30, 150, 80, "judge LLM", "llm", ("reply +", "yes / no question"))
    box(p, 576, 30, 168, 80, "score", "note", ("pass rate", "per category"), bold=True)
    for a, b in ((186, 212), (366, 392), (546, 572)):
        ln(p, a, 70, b, 70, LINE, 1.4, True)
    t(p, 16, 150, "reset memory before every item — the history is the whole context",
      10.5, "#6b7280")
    t(p, 16, 168, "run once (k = 1); report which prompt and tools your agent had",
      10.5, "#6b7280")
    svg("eval-single.svg", W, H, p)


def eval_multi():
    p = []
    W, H = 760, 290
    box(p, 16, 30, 170, 80, "task", "raw", ("user instructions", "+ end-state check"))
    box(p, 236, 30, 150, 80, "user LLM", "llm", ("plays the customer",))
    box(p, 436, 30, 150, 80, "your agent", "out", ("talks + calls tools",), bold=True)
    box(p, 616, 30, 130, 80, "sandbox", "raw", ("tools run here",))
    ln(p, 186, 70, 232, 70, LINE, 1.4, True)
    ln(p, 386, 58, 432, 58, LINE, 1.4, True)
    ln(p, 432, 82, 386, 82, LINE, 1.4, True)
    ln(p, 586, 58, 612, 58, LINE, 1.4, True)
    ln(p, 612, 82, 586, 82, LINE, 1.4, True)
    t(p, 409, 125, "loop until STOP or a turn limit", 10.5, "#6b7280", "middle")
    box(p, 236, 170, 190, 80, "check the end", "llm",
        ("end state == expected?", "rubric for the rest"))
    box(p, 476, 170, 270, 80, "repeat k times", "note",
        ("pass^k — all k must pass", "+ log user-sim errors"), bold=True)
    ln(p, 681, 110, 681, 140, LINE, 1.4)
    ln(p, 681, 140, 331, 140, LINE, 1.4)
    ln(p, 331, 140, 331, 166, LINE, 1.4, True)
    ln(p, 426, 210, 472, 210, LINE, 1.4, True)
    svg("eval-multi.svg", W, H, p)


timeline()
mc_results()
mc_judge()
tau2_dual()
tau2_passk()
tau2_ablation()
ts_userprompt()
eval_single()
eval_multi()
