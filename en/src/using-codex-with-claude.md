# Using Codex as a Subagent in Claude Code

> What you'll learn: how to hand work to a model from another company. Five minutes, hands-on.

Sometimes Claude Code gets stuck. Ask the same model again and it tends to be **wrong the same way**.

That is when a second opinion from a *different* model helps. You can call OpenAI's Codex from inside Claude Code.

---

## 1. Setup

You need the Codex CLI.

```bash
npm install -g @openai/codex
codex login
```

Check it:

```bash
codex --version
# codex-cli 0.149.1
```

A ChatGPT account (free tier included) or an OpenAI API key works, and **usage counts against your Codex limits**, not your Claude ones.

---

## 2. Hands-on — call it directly

Before wrapping anything, **call Codex by hand once.** If that works, everything after it is just packaging.

Make a file with a bug in it:

```bash
mkdir codexlab && cd codexlab
git init -q .                       # ← this matters. See below.

cat > sum.py <<'EOF'
def average(nums):
    return sum(nums) / len(nums)
EOF
```

Ask Codex about it:

```bash
codex exec --sandbox read-only \
  "What input makes average() in sum.py blow up? Answer in one sentence." < /dev/null
```

Real output:

```
I’ll inspect `sum.py` and identify the precise failing input.
exec
/bin/zsh -lc "sed -n '1,240p' sum.py"
 succeeded in 0ms:
def average(nums):
    return sum(nums) / len(nums)

codex
An empty iterable, such as `[]`, makes `average()` raise `ZeroDivisionError`.
```

(The wording varies between runs. As long as the point is the same, it worked.)

**Codex read the file on its own and answered.** With `--sandbox read-only` it can look but not edit — a good default the first time you hand work to someone else's model.

### 🚨 Two things will stop you

**① It refuses to run outside a git repository.**

```
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

Run `git init` first, or pass `--skip-git-repo-check`. It is a guardrail against wrecking files you have no way to recover.

**② Without `< /dev/null` it looks frozen.** Even when the prompt is passed as an argument, Codex still tries to read more from stdin (`Reading additional input from stdin...`). Always close it when calling from a script.

---

## 3. Wrap it as a subagent

Put that command in **one agent file** and you can ask for it in plain language instead.

Create `.claude/agents/codex.md`:

```markdown
---
name: codex
description: When a second pair of eyes from another model would help — root-cause analysis or code review, handed to Codex.
tools: Bash
---

You forward work to Codex. Nothing else.

Pass the user's request to `codex exec` in a single call and report the
output as-is.

    codex exec --sandbox read-only "<request>" < /dev/null

Do not read files or analyse anything yourself. Just forward.
```

Restart Claude Code and you can say:

```
use the codex subagent to review sum.py
```

**The load-bearing line is `tools: Bash`.** Give a subagent Bash and it no longer matters what runs inside it — Codex, or any other CLI.

> **If you would rather not build it,** OpenAI ships a plugin. `/plugin marketplace add openai/codex-plugin-cc` gives you commands like `/codex:review` plus a `codex-rescue` subagent.

---

## Why bother

**A model is wrong in the same places twice.** The odds that I catch what I just missed are poor. A different model fails somewhere else, so its mistakes do not overlap with mine.

That is why this pays off **more for review than for writing code.**

---

## What I did not verify

- The output above is from **codex-cli 0.149.1**. CLI flags move around.
- **I never actually ran the hand-written subagent.** I verified the `codex exec` call and matched the file's frontmatter against the official `codex-rescue` agent — nothing beyond that.
- I did not look into pricing or usage limits. Check Codex's own terms.

---

## Summary

- **`codex exec` is the whole trick.** The subagent only makes it callable in plain language.
- **`git init` first, then `< /dev/null`.** Nearly everyone trips on these two.
- Start with **`--sandbox read-only`**.
- Use it for **review rather than implementation**.
