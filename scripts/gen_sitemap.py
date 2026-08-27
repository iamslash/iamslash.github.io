#!/usr/bin/env python3
"""book/ 아래 빌드 결과로 sitemap.xml 을 만든다.

hreflang 은 **양쪽에 모두 존재하는 페이지에만** 붙인다.
구글 규칙: "If two pages don't both point to each other, the tags will be ignored."
→ 짝이 없는 페이지에 걸면 무시될 뿐 아니라 잘못된 신호가 된다.
"""
import os, sys
from xml.sax.saxutils import escape

BASE = "https://iamslash.github.io"
BOOK = "book"
LANGS = ("en", "ko")
SKIP = {"print.html", "404.html"}


def pages(lang):
    root = os.path.join(BOOK, lang)
    out = set()
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.endswith(".html") or f in SKIP:
                continue
            rel = os.path.relpath(os.path.join(dirpath, f), root)
            out.add(rel.replace(os.sep, "/"))
    return out


def main():
    if not os.path.isdir(BOOK):
        sys.exit("book/ 이 없습니다. 먼저 mdbook build 를 실행하세요.")

    per = {l: pages(l) for l in LANGS}
    both = per["en"] & per["ko"]

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']

    # 언어 선택 페이지
    lines += [f'  <url>', f'    <loc>{BASE}/</loc>',
              f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}/"/>']
    for l in LANGS:
        lines.append(f'    <xhtml:link rel="alternate" hreflang="{l}" href="{BASE}/{l}/"/>')
    lines.append('  </url>')

    paired = unpaired = 0
    for lang in LANGS:
        for p in sorted(per[lang]):
            loc = f"{BASE}/{lang}/{p}"
            lines += ['  <url>', f'    <loc>{escape(loc)}</loc>']
            if p in both:
                paired += 1
                for other in LANGS:
                    alt = f"{BASE}/{other}/{p}"
                    lines.append(f'    <xhtml:link rel="alternate" hreflang="{other}" href="{escape(alt)}"/>')
                lines.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}/"/>')
            else:
                unpaired += 1
            lines.append('  </url>')
    lines.append('</urlset>')

    with open(os.path.join(BOOK, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    with open(os.path.join(BOOK, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")

    print(f"sitemap.xml 생성 — 짝 있는 페이지 {paired}개(hreflang 부여), "
          f"짝 없는 페이지 {unpaired}개(hreflang 생략)")


if __name__ == "__main__":
    main()
