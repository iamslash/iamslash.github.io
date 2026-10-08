# 유명한 문제는 75개입니다

알고리즘 문제를 기억한다는 게 푼 문제를 전부 외운다는 뜻은 아닙니다. 문제 수는
계속 늘어나지만 그 밑에 깔린 **원래 문제**는 그렇게 많지 않습니다. 이름이 붙어
있는 것들이 있고, 새 문제 대부분은 그중 하나를 비튼 겁니다.

그 목록을 가장 깔끔하게 정리해 둔 곳이 Steven Skiena 의 Stony Brook Algorithm
Repository 입니다. 사이트가 스스로를 이렇게 소개합니다 — 가장 근본적인 문제
**75개**의 구현을 모아둔 곳.

## 1. 범주 일곱, 문제 75개

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

**무엇을 다루나**로 나뉩니다. 자료구조, 수, 조합, 도형, 집합과 문자열.
그래프만 둘로 쪼개져 있습니다.

`Polynomial-time` 과 `Hard`. **난이도가 범주 이름에 들어가 있습니다.**

다른 범주에는 이런 게 없습니다. 어려운 문제가 그래프에만 있는 것도 아닙니다 —
`Satisfiability` 는 Combinatorial 에, `Knapsack Problem` 은 Numerical 에 그냥
들어 있습니다.

`Hard` 쪽은 아마 NP-hard 이거나 아직 해결책이 발견되지 않은 문제들일 겁니다.

```
  Polynomial-time   Shortest Path · Minimum Spanning Tree · Topological Sorting ·
                    Connected Components · Matching · Network Flow …

  Hard              Clique · Independent Set · Vertex Cover ·
                    Traveling Salesman · Hamiltonian Cycle · Vertex Coloring …
```

오른쪽에 내 문제가 닿으면 **빠른 알고리즘을 찾는 일을 그만두면 됩니다.** 수십 년간
아무도 못 찾았습니다. 대신 입력이 작다는 걸 이용하거나, 적당히 좋은 답으로
타협하거나, 가지치기로 버팁니다.

어려운 쪽 목록을 더 보고 싶으면 Garey & Johnson 1979 의 부록이 있습니다. 같은
방식으로 적힌 문제가 320개 실려 있습니다. 어려운 문제들은
[NP 는 어려운 문제가 아닙니다](../complexity/p-vs-np.md) 를 참고하세요.

## 2. 한 문제가 적힌 꼴

열어본 항목은 전부 같은 여덟 칸이었습니다. `Topological Sorting` 을 통째로
옮기면 이렇습니다.

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
                      most algorithms on directed acyclic graphs. …

  Implementations     Boost Graph Library (10) · LEDA (9) · JGraphT (8) ·
                      JDSL (8) · goraph (8) …

  Recommended Books   Sedgewick & Schidlowsky, Algorithms in Java ·
                      Cormen et al., Introduction to Algorithms ·
                      Manber, Introduction to Algorithms

  Related Problems    Bandwidth Reduction · Feedback Edge/Vertex Set ·
                      Job Scheduling · Sorting
```

`Implementations` 는 구현할 때 가져다 쓰라고 모아둔 칸입니다.

## 3. 비슷한 문제는 다른 범주에 있습니다

`Topological Sorting` 은 그래프 범주입니다. 그런데 이 문제와 비슷하다고 적혀 있는
문제 넷은 전부 다른 범주에 있습니다.

```
  Topological Sorting           Graph: Polynomial-time
     Sorting                       Combinatorial
     Job Scheduling                Combinatorial
     Bandwidth Reduction           Numerical
     Feedback Edge/Vertex Set      Graph: Hard
```

분류가 잘못된 게 아닙니다. 비슷하다는 걸 전부 범주로 표현하려 들면 범주가 끝없이
늘어납니다. Skiena 는 그렇게 하지 않고, 항목마다 `Related Problems` 를 달아뒀습니다.

그래서 범주는 일곱 가지로 적게 두고, 비슷한 문제는 거기서 따라가면 됩니다.

## 4. 알고리즘이 아니라 문제를 외웁니다

`Dijkstra` 를 외우면 그 알고리즘 하나가 남습니다. 대신 이렇게 외워보십시오.

```
  Input    간선에 가중치가 있는 그래프, 출발점 s, 도착점 t
  Output   s 에서 t 까지 가장 짧은 경로
```

`Shortest Path` 입니다. 지하철 환승도, 배송 경로도, 게임 안의 길찾기도 Input 과
Output 이 저 모양입니다. 하나를 외우면 그 꼴을 한 문제가 전부 걸립니다.

항목이 Input 과 Output 으로 적혀 있는 게 그래서 좋습니다. 새 문제를 만났을 때
맞춰볼 수 있는 꼴이거든요. 알고리즘 이름으로 외우면 그 이름을 떠올린 뒤에야 꺼낼
수 있습니다.

## 5. 책과의 관계

이 목록은 Skiena 의 *The Algorithm Design Manual* 3판 2부 "The Hitchhiker's Guide
to Algorithms" 의 카탈로그를 올린 것입니다. 찾아보고 참고하라고 만든 부분이라고
사이트가 스스로 소개합니다. 2부의 장 일곱 개가 그대로 사이트의 범주 일곱 개입니다.

책 쪽이 더 긴 설명을 담고 있고, 사이트 쪽은 구현 링크가 계속 갱신됩니다.

## 6. 75개의 이름

이름만으로 뭘 하는 문제인지 알기 어려운 것들이 있습니다. Input, Output 은
[75개 전부](./skiena-75.md) 에 한 줄씩 적어뒀습니다.

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

## 출처

- **Stony Brook Algorithm Repository** · `algorist.com`.
  범주 이름과 개수, 6절 목록, 인용한 항목을 여기서 확인했습니다.
- **Skiena 2020** · Steven S. Skiena, *The Algorithm Design Manual*, 3rd edition,
  Springer. 위 목록이 이 책 2부 "The Hitchhiker's Guide to Algorithms" 의
  카탈로그를 올린 것입니다.
- **Garey & Johnson 1979** · Michael R. Garey, David S. Johnson, *Computers and
  Intractability: A Guide to the Theory of NP-Completeness*, W. H. Freeman.
  부록에 320개.
