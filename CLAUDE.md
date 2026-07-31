# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Personal site published to GitHub Pages, built with [mdBook](https://rust-lang.github.io/mdBook/) (a Rust static-site generator). Content is Markdown; there is no application code.

## Commands

```bash
mdbook serve    # live-reload dev server at http://localhost:3000
mdbook build    # build static site into book/ (gitignored)
```

`mdbook` is a Rust binary; install with `cargo install mdbook` if missing. Note the local version may drift from CI — deploys pin **mdBook v0.4.40** (see `.github/workflows/deploy.yml`), so prefer that version when reproducing build behavior.

There are no tests or linters.

## Architecture

- `book.toml` — mdBook config (title, language, `src/` input, `book/` output).
- `src/SUMMARY.md` — the table of contents **and** the router. mdBook only renders pages that are linked here; a new `.md` file under `src/` is invisible until it is added to `SUMMARY.md`. `# Heading` lines in this file become sidebar section separators (e.g. `English`, `한국어`).
- `src/en/` and `src/ko/` — parallel English and Korean content trees. They mirror each other, so a new page usually needs a counterpart in both directories and two entries in `SUMMARY.md`.

## Drafts

`drafts/` holds unpublished blog series (e.g. `drafts/ab-testing/`, `drafts/erlang-to-elixir/`). It sits outside `src/`, so mdBook never builds it — nothing there appears on the site, though the source is visible in the public repo. Each series has a `_PUBLISH.md` tracker with the exact per-post publishing steps and a checklist: move the file into `src/` (e.g. `src/ko/<series>/`), add the prepared line to `src/SUMMARY.md`, check off the entry. Follow the series' own `_PUBLISH.md` rather than improvising, and publish in reading order — posts link to their "next" installment, which 404s until that installment is published.

## Adding a page

1. Create the Markdown file under `src/en/` and/or `src/ko/`.
2. Add a link to it under the matching section in `src/SUMMARY.md` — otherwise it won't appear.

## Commit messages

Write commit messages that describe only the change itself. Do not mention Claude, Claude Code, or any AI assistance — no `Co-Authored-By: Claude` trailer, no "Generated with Claude Code" line, no references in the subject or body.

## Deployment

Pushing to `main` triggers `.github/workflows/deploy.yml`, which builds with mdBook and publishes `book/` to GitHub Pages. There is no manual deploy step.
