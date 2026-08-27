# iamslash.github.io

Personal site built with [mdBook](https://rust-lang.github.io/mdBook/) and published to GitHub Pages.

Korean and English are **two separate mdBook projects** in this one repository, so each language gets its own sidebar, chapter numbering, search index, and `<html lang>`.

## Layout

```
ko/          Korean book   → book/ko   → /ko/...
en/          English book  → book/en   → /en/...
index.html   language selection landing page
scripts/     sitemap generation
```

Filenames match across languages — `ko/src/x.md` and `en/src/x.md` become `/ko/x.html` and `/en/x.html`. The language switcher and the sitemap's `hreflang` both rely on that symmetry.

## Local development

```bash
cargo install mdbook          # deploys pin v0.4.40

mdbook serve ko               # live-reload one language at localhost:3000
mdbook build ko && mdbook build en
```

There is no book at the repository root; always name the language directory.

To reproduce a full deploy locally:

```bash
mdbook build ko && mdbook build en
cp index.html book/
python3 scripts/gen_sitemap.py
```

## Adding a page

1. Create the Markdown file under `ko/src/` **and** `en/src/`, using the same filename in both.
2. Link it from that language's `SUMMARY.md` — mdBook renders nothing that is not listed there.

Nested `SUMMARY.md` entries render as a collapsible tree, which is how multi-post series are grouped:

```markdown
- [Securing My Stack](./secure-my-stack/index.md)
  - [Prologue — Four Doors](./secure-my-stack/00-four-doors.md)
  - [What Is a JWT](./secure-my-stack/01-what-is-jwt.md)
```

## Drafts

Manuscripts live in a separate private repository and only arrive here when they are ready to publish.

Korean is written first; the English version follows once the Korean text has settled. Publishing moves a file into `<lang>/src/` and adds it to that language's `SUMMARY.md`.

## Deployment

Pushing to `main` builds both books, generates `sitemap.xml` and `robots.txt`, and publishes to GitHub Pages via GitHub Actions. There is no manual deploy step.

The repository stays public: GitHub Pages serves from private repositories only on GitHub Pro or higher.
