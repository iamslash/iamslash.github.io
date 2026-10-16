# Multi-turn Agent Eval 1 - You Cannot Write the Answer Key in Advance

A single-turn evaluation is like an exam paper. You ask a question, get an answer, and
compare it to the correct one.

```
  question    What is the capital of France?
  answer      Paris
  correct     Paris                → right
```

An agent does not work like this. It talks with a user who wants to change a flight
over several messages. It asks for the booking number, checks the rules, asks the user
to confirm the change, and then changes the flight.
**Measuring that is multi-turn evaluation.**

Moonshot AI's Kimi K2 technical report (July 2025) also measured multi-turn ability
separately, with three tests: τ2-Bench (June 2025), ACEBench (January 2025) and
MultiChallenge (January 2025).

## 1. There are two kinds of multi-turn evaluation

The difference is **who writes the user's next line**.

```
  scripted conversation   The user's lines are written in advance. The next line is
                          the same even if the agent answers differently
                          Checks whether it reads and understands the earlier
                          conversation                 for example MultiChallenge
  LLM user                An LLM acts as the user, reads the agent's answer and
                          writes the next line
                          Checks whether it finishes the job by sending and
                          receiving messages           for example τ2-Bench
```

Both are multi-turn evaluation. In the first, the agent must remember the earlier
conversation to pass. In the second, it must actually send and receive messages to
finish the task.

## 2. You cannot write the user's next line in advance

Even from the same opening line, the conversation splits depending on the agent's answer.

```
  user      I'd like to move next week's flight one day later
  agent A   Could you give me your booking number?
  user      It's ABC123                               ← this kind of line follows

  agent B   Sure, I've moved it one day later
  user      Wait, which booking did you change?       ← this kind of line follows
```

**The user's second line cannot be written before seeing the agent's first answer.**
So in a scripted conversation test, the user's lines are written in advance. Usually,
the earlier AI answers are written in advance too. In an LLM user test, an LLM plays the
user. With the
first, every agent gets the same user lines, but those lines do not change based on the
agent's answers. With the second, the conversation continues like a real conversation,
but the LLM playing the user also makes mistakes and says something different every
time.

## 3. What to grade is not fixed

There are many ways to do the same job. You can ask for the booking number first or the
name first. So τ-bench (June 2024) does not treat the order of the conversation as the
answer; it **compares the database state after the conversation ends with the expected
state**. It also checks whether the agent gave the user all the required values.

Some conversations have no final state. Asking for advice or editing a piece of writing
are examples. The MultiChallenge (January 2025) paper wrote *"there is no single
ground-truth answer for most test conversations"*. These conversations need a different
way of grading. We look at it in post 3.

## 4. The same task goes differently each time

Since an LLM also plays the user, running the same task again gives a different
conversation. So τ-bench measures **the chance that all k runs of the same task
succeed**. It is called `pass^k`.

```
  pass@k   succeeds at least once in k runs   rises with more tries   common in code evaluation
  pass^k   succeeds in all k runs             falls with more tries   fits customer service
```

On τ-bench's retail domain, gpt-4o has a pass^1 of about 61% but a pass^8 of about 25%.
With one run for each task, it succeeds on about six out of ten tasks. It succeeds on all
eight runs for about one out of four tasks.

## 5. The LLM playing the user makes mistakes too

The τ2-Bench (June 2025) paper counted the user simulator's mistakes by reading the
conversations. A critical error is **a mistake that makes the task impossible to
finish**: asking for something against the user's goal, or leaving things in a state
that cannot be changed back.

```
                                            conversations read   errors      critical errors
  airline (domain taken from τ-bench)       100                  47 (47%)    13 (13%)
  retail (domain taken from τ-bench)        50                   20 (40%)    6 (12%)
  telecom (domain new in τ2-Bench)          50                   8 (16%)     3 (6%)
```

For each percentage, divide the count in that column by the number of conversations read.

**The score of an LLM user test always includes the simulator's mistakes.** That is why
what you tell the user LLM, and how, matters. Post 5 lists those prompts.

## 6. The judge LLM cannot follow the conversation either

Without a final state, an LLM has to read and grade the conversation. A long
conversation can confuse this judge LLM too. The MultiChallenge paper wrote that when
the model judged the whole conversation, it agreed with humans 37% of the time. When a
human wrote one yes / no question for each problem, it agreed 94% of the time.

## So what do you need to decide?

```
  who writes the user's next line   a pre-written record · an LLM playing the user · a human
  how many times the agent answers  once at the end · every turn
  what you grade                    the last answer · the final state · results of many runs
```

In post 6 I suggest how to choose these three things when measuring your own agent.

## Sources

- The month next to a paper's name is the month it first appeared on arXiv.
- **Kimi Team 2025** · *Kimi K2: Open Agentic Intelligence*.
  [`arXiv:2507.20534`](https://arxiv.org/abs/2507.20534).
- **Yao and others 2024** · *τ-bench: A Benchmark for Tool-Agent-User Interaction in
  Real-World Domains*. [`arXiv:2406.12045`](https://arxiv.org/abs/2406.12045).
  Final state comparison, `pass^k`, gpt-4o's 61% · 25%.
- **Barres and others 2025** · *τ2-Bench: Evaluating Conversational Agents in a
  Dual-Control Environment*. [`arXiv:2506.07982`](https://arxiv.org/abs/2506.07982).
  Simulator error counts (Table 2). For the telecom domain's critical errors, the main
  text says 6%, but the note under the table says *"no critical errors were reported"*.
  I followed the main text.
- **Sirdeshmukh and others 2025** · *MultiChallenge*.
  [`arXiv:2501.17399`](https://arxiv.org/abs/2501.17399). How often the model and
  humans gave the same grade: 37.33% · 93.95% (Table 4).
- The flight conversation in section 2 is a made-up example for explanation.
