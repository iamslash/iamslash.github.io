# NP Does Not Mean Hard

## Everyone Says It Wrong

"Can't do it, that's NP." The line usually means one of three things.

| What people say | What is true |
|---|---|
| "It's NP, so you can't solve it fast" | The N in NP does not stand for "no" |
| "NP-hard is a milder NP-complete" | Backwards. NP-hard is far wider |
| "NP-complete means unsolvable" | We solve them daily. Only unlucky inputs drag |

Cook and Levin coined these in 1971, independently, and Karp carried them
forward in 1972. They had one purpose — **to measure how hard a problem is,
and sort it.**

Sorting is not filed under a complexity class. It already has a clear
`O(n log n)` answer. A complexity class is a yardstick built for **problems
nobody has found a good algorithm for.**

## 1. What Counts as Fast

**P** is the set of problems you can solve in polynomial time.

![How running time grows](./complexity-growth.svg)

Both axes are logarithmic, so **every polynomial is a straight line** and
**only the red ones bend upward.** `n³` stays above `2ⁿ` for a while, then gets
passed around n = 10. However big the exponent, a line is still a line. That
one wall is the whole standard.

Three of the names ahead (**P · NP · NP-complete**) attach only to questions
answered "yes" or "no". "Is this number prime?", "Does the maze have a path to
the exit?", "Can I get there by subway in K minutes?" are P. "Give me the
cheapest route", where the answer is a route, gets no such label.

And **solving in polynomial time is not enough to be in P.** Sorting is the
example. Its answer is not yes or no, so it cannot be in P.

## 2. Problems Where Only Brute Force Comes to Mind

You have a stack of receipts.

```
  Of n receipts, can you pick some that add up to exactly X?
```

Any idea? I have none beyond **trying every combination.** Each receipt is
either in or out, so there are 2ⁿ ways.

So I measured it. I set the target to an amount that cannot be reached, which
forces the search to the very end. These are real numbers off a real run.

```
    n   brute force (s)   vs. previous row
   16             0.008                  -
   18             0.031               3.9x     four times for every +2
   20             0.128               4.1x
   22             0.486               3.8x
   24             1.995               4.1x
   26             8.064               4.0x
```

Two more receipts, four times the wait. On the same machine that is 37 hours
at 40 receipts and 4 years at 50 — those two I did not measure, I extended
them from 26. **Fifty receipts. That is not a lot. And it is four years.**

There are plenty more like this. The cheapest tour through every city, an exam
timetable with no clashes, packing a bag.

But **"slow" is not what these have in common.** That is why I am holding off
on a name. What they share is on the **checking side, not the solving side.**

## 3. But Checking Is Fast

While I flail for four years, someone walks up with an answer. "Receipts 3, 7
and 12." How long to check? **Add three numbers. Done.**

```
  solving clock     try every way to choose       2^n steps
  checking clock    add up the answer handed in     n steps
```

Solving looks hopeless, yet **checking is fast every time.** Problems like
this are collected under the name **NP**.

The Clay Mathematics Institute opens its page on the problem with exactly this
idea.

> If it is easy to check that a solution to a problem is correct, is it also
> easy to solve the problem? This is the essence of the P vs NP question.

That is the first paragraph of the Clay Institute's
[P vs NP page](https://www.claymath.org/millennium/p-vs-np/), quoted as is.

The N is not the N of non-polynomial. It is **nondeterministic**. Suppose
someone guesses the answer and I only grade it — the name comes from that
picture.

So **P sits entirely inside NP.** If you can solve it yourself, you can check
it too. Ignore the answer handed to you, solve it again, compare. The primality
test and the maze from section 1 are both in NP.

```
  P ⊆ NP        ⊆ means "sits inside"
```

The symbol `⊆` matters. **Nobody knows whether P is genuinely narrower than
NP.** That question is P vs NP, and it has been open since 1971. It is one of
the Clay Institute's seven Millennium Problems, and their official page puts
the prize at a million dollars each.

## 4. Solving One Problem as Another — Reduction

**Turning problem A into problem B and solving that instead** is called
reduction. The turning has to be fast.

Here is one such problem.

```
  Splitting teams - can these numbers be split into two piles of equal sum?
     e.g.  8, 2, 5, 5   ->   {8, 2} and {5, 5}. Both 10. Yes.
```

The receipt problem in section 2 asked "can you pick some that add up to the
target?" **You can rewrite it as splitting teams.** Throw in two numbers, and
the team-splitting machine solves the receipt problem for you.

```
  receipts   8  3  5  2,  target 10       they add up to 18

  (1) make each side total 19             19 = 18 + 1

  (2) throw in 9 and 11                   9 = 19 - 10,   11 = 19 - 8

        8  3  5  2  9  11                 total 38, half is 19

        {8, 2, 9} = 19      {3, 5, 11} = 19        it splits

        drop the 9 from its side and you have {8, 2}
        8 + 2 = 10 - the answer to the receipt problem
```

**I solved "does it split in half?" and got "can I make 10?" for free.** That
is reduction.

### The One That Takes It On Is Harder

```
  give me one team-splitting machine, and

      it splits teams           its actual job
      it solves receipts too    throw in two numbers and hand it over

  you can turn A into B   ->   B cannot be easier than A

       A = receipts,   B = splitting teams
```

The team-splitting machine took on both problems. So it may be harder, it may
be the same, but it **cannot be easier.**

## 5. All Four Names in One Picture

```
  NP-hard       everything in NP reduces to it
  NP-complete   NP-hard, and in NP itself
```

NP-complete is the **cell where NP and NP-hard overlap.** That is the entire
difference between the two names. And nothing says an NP-hard problem has to
be in NP.

```
                          +------ NP-hard --------------------------------+
  +----- NP --------------+-------------------+                           |
  |                       |                   |                           |
  | +- P ---------------+ | NP-complete       |  Halting problem          |
  | | Is N prime?       | |                   |  Find cheapest route      |
  | | Maze has a path?  | | SAT               |  ^ both outside NP        |
  | | Reach B in K min? | | Subset Sum        |                           |
  | +-------------------+ | Partition         |                           |
  |                       |                   |                           |
  | Factor < K, not 1?    |                   |                           |
  | Two graphs same?      |                   |                           |
  |                       |                   |                           |
  +-----------------------+-------------------+                           |
                          +-----------------------------------------------+
```

Everything in the P cell has been rewritten as a yes/no question. `Subset Sum`
is the receipt problem, `Partition` is splitting teams.

The two at the bottom of the NP cell are factoring and graph isomorphism.
**They are certainly in NP** — hand me an answer and I divide, or match up the
vertices — but **which cell they belong to, nobody has known for decades.** So
they float, in neither box.

**Halting problem** asks "will this program ever stop, or run forever?" It is
not merely hard, it is **impossible.** Turing proved that in 1936. Problems in
NP eventually produce an answer, however slowly; this one does not, so it
cannot be in NP. And yet it is NP-hard. **NP-hard is not a weaker NP-complete.
It is a much wider name.**

## 6. How to Pin Down Your Problem's Complexity Class

```
  (1) see which kind it is, then rewrite it as a yes/no question

       decision      "can it?"             leave it
       search        "give me one"      -> "is there one?"
       optimization  "give me the best" -> "can it be done under K?"

  (2) can you write a checker      ->  it is in NP
  (3) can you write a solver       ->  it is in P
  (4) does a known NP-hard problem
      reduce to your problem       ->  NP-hard

  (5) both (2) and (4)             ->  NP-complete

  (6) go back to the original
       the yes/no version was NP-complete
          ->  the original search / optimization version is NP-hard
```

(2), (3) and (4) are all proved by **building something** — a checker, an
algorithm, a reduction. **If neither (3) nor (4) works, the answer is "not
known yet."** Failing to find something proves nothing — factoring and graph
isomorphism have sat there for decades.

### A Lap with the Traveling Salesman

```
  original     "give me the cheapest route"            optimization
  (1) rewrite  "is there a route costing K or less?"   decision
```

Run (2) through (5) on the rewrite and you get **NP-complete**. Checking is
fast, since you take a route, add the distances and compare to K (2); and
"is there a path through every point exactly once?", already known to be
NP-complete, reduces to it (4).

Now back to the original. **If you have a machine that finds the cheapest
route, you solve the yes/no version just by finding it and comparing to K.**
The yes/no version is NP-complete, so the original is at least that hard.
Hence **NP-hard**. It cannot be NP-complete — the answer is a route, so it
does not qualify for NP.

**The problem you end up calling "NP-hard" out loud is usually this
optimization version.**

### Who Proved the First NP-complete Problem

Step (4) needs a problem that is already known, and at the very start there
isn't one. **The first rung of the ladder cannot be made by reduction.**

Cook did it in 1971 and Levin in 1973, independently. They proved **SAT** is
NP-complete **straight from the definition.** SAT hands you a formula like
`(A or B) and (not A)` and asks whether any combination makes the whole thing
true (A = false, B = true).

**One first NP-complete problem was enough.** After that you only had to keep
reducing out from SAT, and that is how Karp got 21 in 1972 and Garey &
Johnson's 1979 appendix got to 320.

### In Practice You Almost Never Do (4)

Far more often, your problem **already is a problem someone has settled.** Then
you don't write a new reduction, you just take their conclusion.

```
  your problem           the known problem it already is

  delivery ordering   =  traveling salesman   ->  TSP is NP-hard, so this is too
  exam timetabling    =  graph coloring
  job assignment      =  splitting teams
  package versioning  =  SAT
```

**Recognizing "wait, this is the traveling salesman" is the skill you actually
use.**

## 7. Who Made These

| Who | When | What they did |
|---|---|---|
| Hartmanis · Stearns | 1965 | **Made the field itself.** The name "computational complexity", the idea of grouping problems by resource budget (complexity class), the time hierarchy theorem |
| Cobham · Edmonds | 1965 | **Defined P.** Independently proposed "polynomial time = solvable in practice". Hence the Cobham–Edmonds thesis |
| Cook · Levin | 1971 | **Made NP-completeness.** Independently. SAT was the first NP-complete problem |
| Karp | 1972 | **Proved it was useful.** Showed 21 classic problems are all NP-complete, turning a theory into a tool |
| Garey & Johnson | 1979 | **Organized it.** A textbook plus a list of 320, built so a practitioner can look things up |

```
  1965  Hartmanis, Stearns  "group problems by resource budget"  <- the frame
  1965  Cobham, Edmonds     "polynomial time is the line"        <- P
  1971  Cook, Levin         "some groups are fast to check"      <- NP, NP-complete
  1972  Karp                "and it catches 21 real problems"    <- spread
  1979  Garey & Johnson     "320 of them, indexed for lookup"    <- the dictionary
```

The last two invented nothing — they **applied and organized.** That is also
why Karp and Garey & Johnson are famous: they took a concept off the desk and
made it usable by people doing the work.

## 8. Yardsticks Other Than Time

Big-O predates complexity theory by 70 years. The mathematician Paul Bachmann
introduced it in 1894, Landau extended it in 1909, and Knuth brought it into
computer science.

There is also more than one complexity class. The yardstick changes with
**what you count as the resource**, and P and NP are just the "time" one.

```
  time      P, NP, EXP    how many steps it takes
  space     L, PSPACE     how much memory it uses
  random    BPP, RP       if you may flip coins
  quantum   BQP           on a quantum computer
  parallel  NC            if you may use many machines at once
```

This post covers only time because that is what you run into most at work.

## What I Am Not Sure About

- Nobody has proved `P ≠ NP`. The overlap diagram assumes it.
- Cook 1971's five come from a transliteration of the original, and the 320 in
  Garey & Johnson's appendix I counted myself, category by category, from the
  book. Levin 1973's six come from the English translation; Karp 1972's 21
  come from secondary sources.
- What the Clay page confirms is "Cook and Levin formulated P vs NP
  independently in 1971", and no more. Levin 1973 is the publication year.
- The measurements are Python brute force, so absolute times shift with the
  language and the machine. Take only the four-times-per-two-more. The 40 and
  50 figures were not measured — they were extended from 26 (8.064 s) by 2ⁿ.

## Sources

Every number here was counted at the source.

**The people who made the names**

- **Hartmanis · Stearns 1965** · Juris Hartmanis, Richard E. Stearns,
  *On the Computational Complexity of Algorithms*, Transactions of the AMS 117.
  The paper that made the field and its name. The time hierarchy theorem in it
  proves that some cells really are separated. Turing Award 1993.
- **Cobham 1965** · Alan Cobham, *The Intrinsic Computational Difficulty of
  Functions*. Generally credited as the first to single out P.
- **Edmonds 1965** · Jack Edmonds, *Paths, Trees, and Flowers*, Canadian
  Journal of Mathematics 17. Same year, separately. Together they give the
  Cobham–Edmonds thesis.

**NP and NP-complete**

- **Cook 1971** · Stephen A. Cook, *The Complexity of Theorem-Proving
  Procedures*, STOC 1971. The first rung. He lists five problems that look
  hard; of those, primality dropped to P in 2002 and graph isomorphism is
  still open. — [transliteration](http://4mhz.de/cook.html)
- **Levin 1973** · Leonid A. Levin, *Universal Sequential Search Problems*,
  Problems of Information Transmission 9(3), 265–266. Independently of Cook.
  Six problems, phrased as "find one" rather than "does one exist". —
  [English translation](https://www.karlin.mff.cuni.cz/~krajicek/levin.pdf)
- **Karp 1972** · Richard M. Karp, *Reducibility Among Combinatorial Problems*,
  Complexity of Computer Computations, Plenum Press, 85–103. The ladder goes
  up and one paper adds 21. —
  [paper page](https://doi.org/10.1007/978-1-4684-2001-2_9)
- **Garey & Johnson 1979** · Michael R. Garey, David S. Johnson, *Computers and
  Intractability: A Guide to the Theory of NP-Completeness*, W. H. Freeman.
  The first book devoted to NP-completeness. The appendix carries 320, and a
  `(*)` after a name marks that NP membership was never established — that is,
  NP-hard rather than NP-complete.

**Everything else in the post**

- **Turing 1936** · Alan M. Turing, *On Computable Numbers, with an Application
  to the Entscheidungsproblem*, Proc. London Mathematical Society. The proof
  that the halting problem cannot be solved.
- **AKS 2002** · Manindra Agrawal, Neeraj Kayal, Nitin Saxena, *PRIMES is in P*,
  6 August 2002. The day primality dropped into P. Gödel Prize and Fulkerson
  Prize, both 2006.
- **Big-O notation** · Introduced by Paul Bachmann in 1894 and extended by
  Edmund Landau in 1909. Also called Bachmann–Landau notation.
- **Clay Mathematics Institute** ·
  [P vs NP](https://www.claymath.org/millennium/p-vs-np/) ·
  [Millennium Problems](https://www.claymath.org/millennium-problems/).
  The English quotation and the prize figure were checked here.

## More to Watch

- MIT — [6.046 P, NP, NP-completeness, Reductions](https://www.youtube.com/watch?v=eHZifpgyH_4) ·
  [6.006 Computational Complexity](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/resources/lecture-23-computational-complexity/)
