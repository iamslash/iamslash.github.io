# There Are 75 Famous Problems

Remembering algorithm problems does not mean memorizing every problem you have
solved. The number of problems keeps growing, but the **original problems**
underneath them do not. Some of them have names, and most new problems are a
small change to one of those.

The cleanest list of them is Steven Skiena's Stony Brook Algorithm Repository.
The site introduces itself this way — a collection of implementations for the
**75** most fundamental problems.

## 1. Seven Categories, 75 Problems

```
  Data Structures                   6
  Numerical Problems               11
  Combinatorial Problems           10
  Graph: Polynomial-time Problems  12
  Graph: Hard Problems             11
  Computational Geometry           16
  Set and String Problems           9
                                   --
                                   75
```

The split is by **topic**. Data structures, numbers, combinatorics, geometry,
sets and strings. Only graphs are cut in two.

`Polynomial-time` and `Hard`. **Difficulty is in the category name.**

No other category does this. And the hard problems are not only in graphs —
`Satisfiability` just sits in Combinatorial, `Knapsack Problem` just sits in
Numerical.

The `Hard` side is probably NP-hard problems, or ones nobody has solved yet.

```
  Polynomial-time   Shortest Path . Minimum Spanning Tree . Topological Sorting .
                    Connected Components . Matching . Network Flow ...

  Hard              Clique . Independent Set . Vertex Cover .
                    Traveling Salesman . Hamiltonian Cycle . Vertex Coloring ...
```

If your problem is on the `Hard` side, **stop looking for a fast algorithm.**
No one has found one in decades. Instead, rely on the input being small, take
an answer that is good enough, or get by with pruning.

A longer list of the hard ones is in the appendix of Garey & Johnson 1979. It
has 320 problems written the same way. For the hard problems, see [NP Does Not
Mean Hard](../complexity/p-vs-np.md).

## 2. What One Entry Looks Like

Every entry I opened had the same eight fields. Here is `Topological Sorting`
copied out in full.

```
  Topological Sorting

  Input  [figure]     dots scattered, arrows running every which way
  Output [figure]     dots in one row, every arrow pointing right

  Input Description   A directed, acyclic graph G=(V,E)
                      (also known as a partial order or poset).

  Problem             Find a linear ordering of the vertices of V such that
                      for each edge (i,j) in E, vertex i is to the left of
                      vertex j.

  Excerpt             Topological sorting arises as a natural subproblem in
                      most algorithms on directed acyclic graphs. ...

  Implementations     Boost Graph Library (10) . LEDA (9) . JGraphT (8) .
                      JDSL (8) . goraph (8) ...

  Recommended Books   Sedgewick & Schidlowsky, Algorithms in Java .
                      Cormen et al., Introduction to Algorithms .
                      Manber, Introduction to Algorithms

  Related Problems    Bandwidth Reduction . Feedback Edge/Vertex Set .
                      Job Scheduling . Sorting
```

`Implementations` is there so that when you build something, you can get code
for it.

## 3. Similar Problems Live in Other Categories

`Topological Sorting` is in a graph category. But all four problems listed as
similar to it are in other categories.

```
  Topological Sorting           Graph: Polynomial-time
     Sorting                       Combinatorial
     Job Scheduling                Combinatorial
     Bandwidth Reduction           Numerical
     Feedback Edge/Vertex Set      Graph: Hard
```

The grouping is not wrong. If you made a new category every time two problems
looked alike, the categories would never stop growing. Skiena did not do that.
He put a `Related Problems` field on every entry instead.

So the categories stay few — seven — and you follow similar problems from
there.

## 4. Memorize Problems, Not Algorithms

Memorize `Dijkstra` and all you have is one algorithm. Try memorizing this
instead.

```
  Input    a graph with weights on the edges, a start s, a target t
  Output   the shortest path from s to t
```

That is `Shortest Path`. A subway transfer, a delivery route, pathfinding in a
game — the Input and Output all have that shape. Memorize one and you
recognize every problem shaped like it.

That is why writing entries as Input and Output is good. You can hold a new
problem up against that shape and compare. Memorize by algorithm name and you
can only use it after the name comes to mind.

## 5. The Book It Came From

This list is the catalog from Part II of Skiena's *The Algorithm Design
Manual*, 3rd edition — "The Hitchhiker's Guide to Algorithms" — put online.
The site says that part was made for looking things up. The seven chapters of
Part II are the seven categories on the site.

The book has longer explanations; the site keeps its implementation links up
to date.

## 6. The 75 Names

Some names make it hard to tell what the problem is. The Input and Output for
[all 75](./skiena-75.md) are written out one line each.

```
  Data Structures
     Dictionaries
     Priority Queues
     Suffix Trees and Arrays
     Graph Data Structures
     Set Data Structures
     Kd-Trees

  Numerical Problems
     Solving Linear Equations
     Bandwidth Reduction
     Matrix Multiplication
     Determinants and Permanents
     Constrained and Unconstrained Optimization
     Linear Programming
     Random Number Generation
     Factoring and Primality Testing
     Arbitrary-Precision Arithmetic
     Knapsack Problem
     Discrete Fourier Transform

  Combinatorial Problems
     Sorting
     Searching
     Median and Selection
     Generating Permutations
     Generating Subsets
     Generating Partitions
     Generating Graphs
     Calendrical Calculations
     Job Scheduling
     Satisfiability

  Graph: Polynomial-time Problems
     Connected Components
     Topological Sorting
     Minimum Spanning Tree
     Shortest Path
     Transitive Closure and Reduction
     Matching
     Eulerian Cycle/Chinese Postman
     Edge and Vertex Connectivity
     Network Flow
     Drawing Graphs Nicely
     Drawing Trees
     Planarity Detection and Embedding

  Graph: Hard Problems
     Clique
     Independent Set
     Vertex Cover
     Traveling Salesman Problem
     Hamiltonian Cycle
     Graph Partition
     Vertex Coloring
     Edge Coloring
     Graph Isomorphism
     Steiner Tree
     Feedback Edge/Vertex Set

  Computational Geometry
     Robust Geometric Primitives
     Convex Hull
     Triangulation
     Voronoi Diagrams
     Nearest Neighbor Search
     Range Search
     Point Location
     Intersection Detection
     Bin Packing
     Medial-Axis Transform
     Polygon Partitioning
     Simplifying Polygons
     Shape Similarity
     Motion Planning
     Maintaining Line Arrangements
     Minkowski Sum

  Set and String Problems
     Set Cover
     Set Packing
     String Matching
     Approximate String Matching
     Text Compression
     Cryptography
     Finite State Machine Minimization
     Longest Common Substring/Subsequence
     Shortest Common Superstring
```

## Sources

- **Stony Brook Algorithm Repository** · `algorist.com`.
  The category names and counts, the list in section 6, and the quoted entry
  were all checked here.
- **Skiena 2020** · Steven S. Skiena, *The Algorithm Design Manual*, 3rd
  edition, Springer. The list above is the catalog from Part II of this book,
  "The Hitchhiker's Guide to Algorithms", put online.
- **Garey & Johnson 1979** · Michael R. Garey, David S. Johnson, *Computers and
  Intractability: A Guide to the Theory of NP-Completeness*, W. H. Freeman.
  320 in the appendix.
