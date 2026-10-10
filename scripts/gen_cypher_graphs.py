#!/usr/bin/env python3
"""neo4j-cypher 시리즈의 node/edge 그림을 SVG 로 그린다.

의존성 없음, 돌리면 결과가 매번 같다. 두 언어 트리에 같은 파일을 쓴다.

    python3 scripts/gen_cypher_graphs.py
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTS = [os.path.join(ROOT, lang, "src", "neo4j-cypher") for lang in ("ko", "en")]

def write(name, text):
    for d in OUTS:
        open(os.path.join(d, name), "w").write(text)
import math

PAL = {  # 종류별 색
 "Person": ("#e9f1fb", "#3b6ea5"),
 "Place":  ("#fdf1e6", "#b5733a"),
 "City":   ("#edf5ec", "#4a7c4e"),
}
FONT = "ui-monospace,Menlo,monospace"
H = 40

def nw(label):            # 글자 수로 너비
    return max(84, 13 + 8.2 * len(label))

class G:
    def __init__(self, w, h):
        self.w, self.h, self.n, self.parts = w, h, {}, []
    def node(self, nid, label, kind, x, y):
        self.n[nid] = (x, y, nw(label), H, label, kind)
    def _port(self, a, b):
        ax, ay, aw, ah, *_ = self.n[a]; bx, by, bw, bh, *_ = self.n[b]
        acx, acy, bcx, bcy = ax+aw/2, ay+ah/2, bx+bw/2, by+bh/2
        if abs(bcx-acx) > abs(bcy-acy):
            return ((ax+aw, acy) if bcx > acx else (ax, acy),
                    (bx, bcy) if bcx > acx else (bx+bw, bcy))
        return ((acx, ay+ah) if bcy > acy else (acx, ay),
                (bcx, by) if bcy > acy else (bcx, by+bh))
    def edge(self, a, b, label, dy=-7, dx=0):
        (x1,y1),(x2,y2) = self._port(a,b)
        ux, uy = x2-x1, y2-y1; d = math.hypot(ux,uy) or 1
        x2 -= ux/d*9; y2 -= uy/d*9
        self.parts.append(
          f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
          f'stroke="#9aa3b0" stroke-width="1.4" marker-end="url(#a)"/>')
        mx, my = (x1+x2)/2+dx, (y1+y2)/2+dy
        self.parts.append(
          f'<text x="{mx:.0f}" y="{my:.0f}" font-size="11" fill="#6b7280" '
          f'text-anchor="middle">{label}</text>')
    def svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
               f'height="{self.h}" viewBox="0 0 {self.w} {self.h}" font-family="{FONT}">',
               '<defs><marker id="a" viewBox="0 0 10 10" refX="9" refY="5" '
               'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
               '<path d="M0,0 L10,5 L0,10 z" fill="#9aa3b0"/></marker></defs>',
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>']
        out += self.parts
        for x,y,w,h,label,kind in self.n.values():
            fill, stroke = PAL[kind]
            out.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="9" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')
            out.append(f'<text x="{x+w/2:.0f}" y="{y+17}" font-size="12.5" fill="#1f2430" '
                       f'text-anchor="middle">{label}</text>')
            out.append(f'<text x="{x+w/2:.0f}" y="{y+31}" font-size="9.5" fill="{stroke}" '
                       f'text-anchor="middle">:{kind}</text>')
        out.append('</svg>')
        return "\n".join(out)

# ---- 1편: 친구 그래프
g = G(600, 190)
g.node("mina","Mina","Person", 30, 24)
g.node("jun","Jun","Person", 240, 24)
g.node("hana","Hana","Person", 440, 24)
g.node("tae","Tae","Person", 240, 126)
g.edge("mina","jun","KNOWS"); g.edge("jun","hana","KNOWS")
g.edge("mina","tae","KNOWS", dy=-6, dx=-4)
write("friends.svg", g.svg())

# ---- 2편: 식당 그래프
g2 = G(820, 230)
g2.node("me","me","Person", 20, 90)
g2.node("mina","Mina","Person", 180, 24)
g2.node("jun","Jun","Person", 180, 156)
g2.node("olive","Olive Table","Place", 380, 24)
g2.node("cork","Cork and Candle","Place", 380, 156)
g2.node("lisbon","Lisbon","City", 660, 90)
g2.edge("me","mina","LIKES", dy=-16, dx=-14)
g2.edge("jun","mina","TRAINED_UNDER", dy=2, dx=-50)
g2.edge("mina","olive","COLLAB_WITH")
g2.edge("jun","cork","BUILT_WINE_LIST")
g2.edge("olive","lisbon","IN", dy=-8)
g2.edge("cork","lisbon","IN", dy=-8)
write("restaurants.svg", g2.svg())
print("ko/ 와 en/ 양쪽에 그렸습니다")
