# Multi-turn Agent Eval 6 - Measure Your Agent Twice: Scripted, Then With an LLM User

A scripted conversation shows whether the agent remembers what was said earlier,
and an LLM user shows whether it finishes the task.

Here is a **proposal** that combines methods from the earlier
papers — τ-bench (June 2024), ToolSandbox (August 2024), MultiChallenge (January
2025), τ2-Bench (June 2025). None of the papers recommends this exact order. The
name next to each step is the paper the method comes from.

## 1. Scripted conversation — does it remember what was said earlier?

<img src="./eval-single.svg" alt="Scripted conversation evaluation. A fixed conversation history goes in, the agent writes one answer, and a judge LLM grades it seeing only the answer and a yes/no question" style="max-width:760px; width:100%; height:auto; display:block; margin:0 auto;">

```
  1  Build the problem   in a real conversation from your service, find a user
                         turn where earlier information or instructions are
                         needed. End the conversation history at that turn
  2  Add a question      one question that can be judged yes / no from the
                         answer alone                                       MultiChallenge
  3  Get the answer      clear the agent's memory, give it the conversation
                         history, get one answer
  4  Judge               give the judge LLM only the answer and the
                         question. Not the conversation                     MultiChallenge
  5  Count               pass rate for each category. Run once
```

For step 1, use MultiChallenge's four categories as a checklist.

```
  Does it follow the first turn's instruction until the end   "From now on, answer in three lines"
  Does it use information the user mentioned only briefly     "I would like it to be within a 5-minute walk"
  Does it edit the right version of a text that has been changed many times
  Does it keep its correct answer even when the user doubts it
```

Step 2 matters most. **Ask a question like "does the answer have nuts?" rather
than "is this a good answer?"** In MultiChallenge, the judge agreed with people
37% of the time when given the whole conversation. With just one question, it
agreed 94% of the time.

**Check the judge LLM once before trusting it.** Have a person grade about 50
problems. Then check how often the judge LLM gives the same grade. MultiChallenge
also checked its grades against people's grades before using automatic grading.

**You can also run a public test first.** MultiChallenge's 273 problems and grading
code are public. Post 3 explains how to add your agent.

## 2. LLM user — does it finish the task?

<img src="./eval-multi.svg" alt="LLM user evaluation. A user LLM given a task talks with the agent, and the agent calls tools in a sandbox. At the end the final state is checked, and repeating k times gives pass^k" style="max-width:760px; width:100%; height:auto; display:block; margin:0 auto;">

```
  1  Write the task         user instruction + what the final state
                            must be                                         τ2-Bench format
  2  Build a sandbox        make the agent's tools change a fake DB
                            instead of the real one                         τ-bench
  3  Set up the user LLM    the rules from post 5 + knowledge boundary
                            + demonstration                                 ToolSandbox
  4  Run the conversation   until the user sends an end signal or the
                            conversation reaches the turn limit
  5  Grade                  does the final state match the answer? Use
                            yes / no questions only to check things the
                            state cannot show                               τ2-Bench
  6  Run k times            report pass^1 and pass^k together               τ-bench
  7  Count simulator        read a few failed conversations and mark
     errors                 failures that were the user's fault             τ2-Bench
```

For step 1, use τ2-Bench's task format without changing it.

```
  user_scenario         seen only by the user LLM
    reason_for_call       why the user contacted support
    known_info            what the user knows (name, reservation number)
    task_instructions     if the agent does this, do that
  evaluation_criteria   used only for grading
    required final state     the DB must change like this
    information to tell      this value must be told to the user
    the user
```

**In step 6, setting k to about 4 is enough.** τ2-Bench also ran each task four times.
Looking only at pass^1 does not show whether a success happened just by luck. For
an agent that deals with customers, pass^4 is closer to reality.

**Run one more comparison.** As τ2-Bench does, let the agent solve the task without
a user, with all the tools available, and compare the scores. If it cannot solve the
task even alone, check **reasoning and tool use** first. If it solves it alone but
fails with the user, check **how it explains things and guides the user** first.
Read the failed conversations to check the cause.

**You can also run a public test first.** If you add your agent as a
`HalfDuplexAgent`, the τ2-Bench repository runs the user simulator and the grading
for you. Post 4 explains how.

## 3. What to report with the results

For the same agent, the score changes when any of these change.

```
  agent         model, system prompt, tools turned on, whether a memory system is on
  user side     user model and user prompt (for a scripted conversation, where
                the conversation history came from)
  judge side    judge model, judge prompt, how often the judge agrees with people
  how it ran    k, temperature, number of failures that look like the simulator's
                fault (separate from the raw score)
```

## 4. Which one first

```
  An assistant that learns what the user        scripted conversation first.
  needs through conversation                    You can see what information it misses
  An agent that uses tools to finish tasks      LLM user first. You can grade it
                                                directly from the final state
```

Either way, **don't guess multi-turn ability from a single-turn score.** MINT
(September 2023) wrote that a model can do well in one turn but poorly over
multiple turns. Lost in Conversation (May 2025) wrote that when the same task was
split across multiple turns, recent models' scores fell by 39% on average.

## Sources

- This post is a proposal. The paper behind each step is named next to the step,
  and the numbers were checked against the originals in the earlier posts.
- **MultiChallenge** · [`arXiv:2501.17399`](https://arxiv.org/abs/2501.17399).
  Four categories, yes / no question, 37% · 94%.
- **τ-bench** · [`arXiv:2406.12045`](https://arxiv.org/abs/2406.12045). Fake DB and
  final state, pass^k.
- **ToolSandbox** · [`arXiv:2408.04682`](https://arxiv.org/abs/2408.04682). Knowledge
  boundary and demonstration.
- **τ2-Bench** · [`arXiv:2506.07982`](https://arxiv.org/abs/2506.07982). Task format
  (the repository's `tasks.json`), four runs, solving without a user, counting
  simulator errors.
- **MINT** · [`arXiv:2309.10691`](https://arxiv.org/abs/2309.10691).
- **Lost in Conversation** · [`arXiv:2505.06120`](https://arxiv.org/abs/2505.06120).
- The two figures are drawn by `scripts/gen_multiturn_charts.py`.
