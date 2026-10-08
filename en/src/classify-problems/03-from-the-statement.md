# In an Interview, Nobody Tells You the Name

The table in [There Are 55 Coding Interview Problems](./02-my-catalog.md)
reads left to right. The entry name comes first, and the Input and Output sit
next to it.

An interview is the opposite. **You get one problem statement, and no entry
name comes with it.** So for the list to be usable, it has to read right to
left as well.

## 1. What You Can See in the Statement

Some things stand out as you read a statement. Not algorithm names — **things
that are simply written there**.

| If the statement says | Candidates | Splitting question |
|---|---|---|
| it is sorted · you may sort it | Two ends moving in · Boundary by monotonicity | are you finding a pair or finding a boundary |
| a contiguous run | Window over a sequence · Largest run | a run that satisfies a condition, or a run with the largest sum |
| the longest thing that only goes up | Longest increasing subsequence | must it be contiguous |
| the first larger or smaller thing at each position | Next greater element | if an earlier element is smaller than the current one, is it useless forever |
| ranges asked about many times | Prefix and range | do values change in between |
| the kth | Kth element · Pull the best one next | asked once, or asked over and over |
| the two or three that sum to the target | Pair with target | may you sort |
| how many times · a majority · a missing value | Count and tally | is the range of values narrow |
| you have to decide how to sort it first | Sort then scan | does fixing one criterion make the rest simple |
| things with a start and an end | Intervals | sort by start, or sort by end |
| some tasks must come first | Topological order | a cycle means there is no answer |
| islands · blobs · are these two in the same blob | Connected components | do the edges arrive all at once or one at a time |
| is there a cycle | Cycle | is there one next, or several branches |
| cheapest way to connect everything · most you can push | Spanning and flow | does it split into two sides |
| least cost · fewest steps | Shortest path | are all weights 1, are any negative |
| a grid | Walk a grid · Grid DP · Simulate on a grid | does it spread, go one way only, or repeat a rule |
| a table sorted along every row and every column | Search a sorted grid | is it still sorted if you flatten it into one row |
| rotate or flip the matrix | Transform in place | must you use no extra space |
| a tree | Walk a tree · Tree DP | does one pass finish it, or do you choose for each subtree on the way up |
| traversal output is given | Build a tree | where in the input is the root |
| a tree with smaller on the left, larger on the right | Binary search tree | do you build the sorted sequence, or pull it out |
| the common ancestor of two nodes | Lowest common ancestor | can you use the sorted property |
| a palindrome | Palindrome | do you expand from the middle or close in from both ends |
| brackets or operators | Brackets and expressions | is there nesting |
| two strings or two arrays | Edit distance · Common subsequence | the cost of fixing, or the thing they share |
| find a piece inside a long text | Pattern in text | is there more than one piece |
| words starting with this prefix | Prefix set | are the queries repeated |
| are the letters just in a different order | Same letters | are you only checking whether two match, or grouping all of them |
| rewrite it by a rule | Rewrite a string | does the rule finish in one pass, or apply again to what came out |
| you choose at every step | Carry state forward | do you know the number of states in advance, or does it grow with the input |
| how many ways | Count the ways · Combinatorics | count up one step at a time, or count it all at once with a formula |
| you merge intervals as you go | Interval DP | does it split on what you do last |
| you choose against a limit or a target | Knapsack | do you use the same item more than once |
| show me every arrangement | List every arrangement | can you prune |
| the set of what you picked is the state | Small n, every subset | is the subset enough as state, or must you carry where you are too |
| players take turns | Win or lose | does the board split into independent piles |
| everything is paired except one | Bit tricks | how many of each are paired up |
| primes · divisors · multiples | Divisors and primes | do you look at one number, or at a range |
| bases · digits · very large numbers | Digits and bases | does it go past the type range |
| draw at random | Chance and sampling | do you know the total size in advance |
| a list of operations and a time limit | Design a structure | do you do the work on the way in, or on the way out |
| throw something away when it is full | Cache and eviction | is the eviction rule time or count |
| you push and pop at one end only | Stack and queue discipline | do they also ask for something like the minimum |
| insert, delete and lookup must all be fast | Key to value | is there also a random pick |
| hand them to me one at a time | Iterate on demand | may you expand everything in advance |
| the nodes are chained together | Linked list surgery | do you know the length in advance |

The left column is **visible before you know the answer.** You can only reach
`Monotonic Stack` after monotonic stacks have already come to mind. "The first
larger thing at each position" is simply written in the statement.

**One of part 2's 55 is missing here.** `Geometry` has no signal you can
recognize in a statement beyond "a shape shows up". It is worth knowing that
some entries have a weak signal — for those, the only way is to know them on
sight.

## 2. The Constraints Are Part of the Statement

When the size of `n` is written down, the complexity of the answer is nearly
settled.

```
  n <= 20          2^n           look at every subset
  n <= 40          2^(n/2)       split in half and meet
  n <= 500         n^3
  n <= 5,000       n^2
  n <= 10^5        n log n       sorting . binary search . heap . segment tree
  n <= 10^7        n             one pass
  values to 10^9   log(value) or math    the number itself is large, not its size
```

But this **narrows it down; it does not settle it.** With `n <= 20` it could
be bitmask DP or it could be plain backtracking. It only cuts the candidates
down to a few.

## 3. When There Is More Than One Candidate

This is where it really starts. When the signal has narrowed it to two or
three and you do not know which to use, ask in this order.

```
  (1) what does it look like if you just try everything
  (2) why is that slow
  (3) what do you not have to redo
  (4) so what do you use
  (5) why is that correct
```

Try `the shortest run whose sum is at least K`.

```
  (1)  look at every run                        n^2
  (2)  every time the left end moves, you add the sum up from scratch
  (3)  the left end never has to go back -- extend right, then pull left
  (4)  sliding window
  (5)  once the sum reaches K you may pull the left in, and when it is too
       small you must extend the right. Neither side ever moves backwards,
       so you look at each element at most twice
```

**(3) is the answer.** The rest are questions for getting there.

And if (3) does not come, you do not know that problem yet. Whether the name
came to mind has nothing to do with it. You can say "sliding window" and still
be stuck the moment the problem changes a little, if you cannot do (3).

**Mix in negative numbers and (3) breaks.** Pulling the left in is no longer
guaranteed to make the sum go down. That is why the `splitting question` for
this entry is written the way it is.

## 4. How To Review

```
  cover the right, look only at the left   recall in this order: signal -> candidates -> splitting question
  get stuck? say (1) to (5) out loud       find out if you get stuck at (3) or at (4)
  look at the ones you got wrong more often
  come back later to the ones you got right   of course you get it right if you look again right away
```

When you mix, mix **the ones you confuse with each other.** Not a random
shuffle. `Window over a sequence` and `Largest run` have almost **the same**
Input and Output — put those two side by side. There is one question to ask:
*why does this one use that method when the one next to it does not?*

### Mixing Makes You Worse While You Practice

Someone measured this with math problems. They taught 18 college students how
to find the volume of four unfamiliar solids. One group practiced **grouped by
type**, the other **with the four types mixed together.** Same problems, same
count, only the order was different.

```
  during practice         grouped  89%     mixed  60%
  test one week later     grouped  20%     mixed  63%
```

**The reason they got them wrong matters.** The grouped side did not make
arithmetic errors — they **picked the wrong formula.** When they picked the
right formula, they nearly always got the right answer.

Practice in a block and you never have to choose which kind of problem it is.
You are told in advance. Do ten `Largest run` problems in a row and you start
all ten knowing the answer. In an interview nobody tells you.

And yet **the grouped side does better while practicing.** 89% against 60%. So
mixing feels worse. In another experiment, where people had to name the
painter of a painting, 78% of the 120 participants did better when the
paintings were mixed. And 78% said grouping was as good or better. They still
said that after taking the test. **What it feels like is the opposite of what
works.**

Both were measured on undergraduates in a lab. Rohrer & Taylor listed four
limits of their own experiment. One of them matters most for interviews: **the
test problems had the same shape as the practice problems. So they did not
measure whether mixing still helps on a problem you have never seen before.**

And **say it out loud.** An interview is not a test of solving. It is a test
of showing how you solve, and if you only ever practice quietly on your own,
that part never gets trained. Saying (1) through (5) out loud reviews the
problem and practices talking at the same time.

## Sources

- **Rohrer & Taylor 2007** · Doug Rohrer, Kelli Taylor, "The shuffling of
  mathematics problems improves learning", *Instructional Science* 35:481-498.
  The figures above are from Experiment 2.
- **Kornell & Bjork 2008** · Nate Kornell, Robert A. Bjork, "Learning Concepts
  and Categories: Is Spacing the 'Enemy of Induction'?", *Psychological Science*
  19(6):585-592. The figures above are from Experiment 1a.
