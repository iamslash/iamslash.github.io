# drafts

Unpublished manuscripts. **They have not been verified.**

mdBook never builds this directory, so nothing here appears on the site — but
the source is visible in this public repository. Treat it accordingly:

> **Do not follow anything in here.** Code, configuration, and quotes change
> throughout review, and drafts have carried outright errors for days at a
> time — a database setting that crashed the app at startup, a quote attributed
> to the wrong product's documentation, a summary that contradicted its own
> table two sections earlier. Every one of those was caught *after* it was
> written down.

Published posts live at <https://iamslash.github.io>.

## Layout

```
drafts/<series>/           Korean manuscripts (the source of truth)
drafts/<series>/_PUBLISH.md  per-series tracker: publishing steps and state
```

Korean is written first. English versions are written afterwards, once the
Korean text has settled, so the same correction is not made twice.

## Evidence labels

Posts in the technical series tag each claim with where it came from:

| Label | Meaning |
|---|---|
| `[관찰]` | Ran it. Output shown is real output. |
| `[문서]` | Verbatim quote from vendor documentation. |
| `[추론]` | Inferred from the above — not directly verified. |

Each post ends with a **"확인 못 한 것"** section listing what could not be
confirmed. The labels are only worth having if they are honest: never add one
to satisfy the convention, and check whether an answer is already in a source
you cited before writing that you could not find it.
