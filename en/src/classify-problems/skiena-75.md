# All 75

The list from [There Are 75 Famous Problems](./01-skiena-catalog.md), with one
line of **Input and Output** for each problem. Many names do not tell you what the problem is.

These are my own short versions, not the originals. The exact definitions
are in each entry of the Stony Brook Algorithm Repository (`algorist.com`).


## Data Structures

| Problem | In | Out |
|---|---|---|
| [Dictionaries](https://www.algorist.com/problems/Dictionaries.html) | n records, each with a key | a structure that finds, inserts and deletes a record by its key |
| [Priority Queues](https://www.algorist.com/problems/Priority_Queues.html) | records with ordered keys | a structure that always hands back the smallest, and stays fast as records come and go |
| [Suffix Trees and Arrays](https://www.algorist.com/problems/Suffix_Trees_and_Arrays.html) | a reference string | a structure that finds every place a query string sits inside it |
| [Graph Data Structures](https://www.algorist.com/problems/Graph_Data_Structures.html) | a graph | a representation that is small to store and quick to walk |
| [Set Data Structures](https://www.algorist.com/problems/Set_Data_Structures.html) | a universe of objects and a family of subsets | a representation that tests membership and takes unions and intersections quickly |
| [Kd-Trees](https://www.algorist.com/problems/Kd-Trees.html) | n points in k dimensions | a tree splitting the space so each point sits in its own region |

## Numerical Problems

| Problem | In | Out |
|---|---|---|
| [Solving Linear Equations](https://www.algorist.com/problems/Solving_Linear_Equations.html) | a matrix A and a vector b | the x with A·x = b |
| [Bandwidth Reduction](https://www.algorist.com/problems/Bandwidth_Reduction.html) | a graph that represents a sparse matrix | the ordering of vertices that makes the longest edge as short as possible |
| [Matrix Multiplication](https://www.algorist.com/problems/Matrix_Multiplication.html) | two matrices | their product |
| [Determinants and Permanents](https://www.algorist.com/problems/Determinants_and_Permanents.html) | an n x n matrix | its determinant, or its permanent |
| [Constrained and Unconstrained Optimization](https://www.algorist.com/problems/Constrained_and_Unconstrained_Optimization.html) | a function of n variables | the point where it is largest, or smallest |
| [Linear Programming](https://www.algorist.com/problems/Linear_Programming.html) | linear inequalities and a linear objective | values that satisfy all of them and make the objective as large as possible |
| [Random Number Generation](https://www.algorist.com/problems/Random_Number_Generation.html) | nothing, or a seed | a sequence of integers that behaves like a random one |
| [Factoring and Primality Testing](https://www.algorist.com/problems/Factoring_and_Primality_Testing.html) | an integer n | whether n is prime, and if not, its factors |
| [Arbitrary-Precision Arithmetic](https://www.algorist.com/problems/Arbitrary-Precision_Arithmetic.html) | two integers too big for a machine word | their sum, difference, product and quotient |
| [Knapsack Problem](https://www.algorist.com/problems/Knapsack_Problem.html) | items with a size and a value, and a capacity | the subset of greatest value that still fits |
| [Discrete Fourier Transform](https://www.algorist.com/problems/Discrete_Fourier_Transform.html) | n values sampled from a function at even intervals | the same signal written as a sum of frequencies |

## Combinatorial Problems

| Problem | In | Out |
|---|---|---|
| [Sorting](https://www.algorist.com/problems/Sorting.html) | n items | the same items in increasing order |
| [Searching](https://www.algorist.com/problems/Searching.html) | n keys and a query key | where the query sits among them |
| [Median and Selection](https://www.algorist.com/problems/Median_and_Selection.html) | n numbers | the one with half below it and half above |
| [Generating Permutations](https://www.algorist.com/problems/Generating_Permutations.html) | an integer n | every ordering of n things, or a random one, or the next one |
| [Generating Subsets](https://www.algorist.com/problems/Generating_Subsets.html) | an integer n | every subset of 1..n, or a random one, or the next one |
| [Generating Partitions](https://www.algorist.com/problems/Generating_Partitions.html) | an integer n | every way to split n, or a random one, or the next one |
| [Generating Graphs](https://www.algorist.com/problems/Generating_Graphs.html) | a vertex count, an edge count, or an edge probability | a graph that meets them — every such graph, a random one, or the next |
| [Calendrical Calculations](https://www.algorist.com/problems/Calendrical_Calculations.html) | a month, a day and a year | the weekday it fell on |
| [Job Scheduling](https://www.algorist.com/problems/Job_Scheduling.html) | jobs with "this one before that one" constraints | a schedule finishing in the least time, or on the fewest machines |
| [Satisfiability](https://www.algorist.com/problems/Satisfiability.html) | clauses built from ands, ors and nots on boolean variables | whether some assignment makes every clause true |

## Graph: Polynomial-time Problems

| Problem | In | Out |
|---|---|---|
| [Connected Components](https://www.algorist.com/problems/Connected_Components.html) | a graph and a start vertex | every vertex and edge reachable from it |
| [Topological Sorting](https://www.algorist.com/problems/Topological_Sorting.html) | a directed acyclic graph | the vertices in a row with every edge pointing right |
| [Minimum Spanning Tree](https://www.algorist.com/problems/Minimum_Spanning_Tree.html) | a graph with weighted edges | the cheapest set of edges that still connects everything |
| [Shortest Path](https://www.algorist.com/problems/Shortest_Path.html) | a weighted graph, a start s and an end t | the cheapest route from s to t |
| [Transitive Closure and Reduction](https://www.algorist.com/problems/Transitive_Closure_and_Reduction.html) | a directed graph | an edge wherever a path exists, or the fewest edges that still let you reach the same places |
| [Matching](https://www.algorist.com/problems/Matching.html) | a graph, possibly weighted | the largest set of edges sharing no vertex |
| [Eulerian Cycle / Chinese Postman](https://www.algorist.com/problems/Eulerian_Cycle_Chinese_Postman.html) | a graph | the shortest tour using every edge at least once |
| [Edge and Vertex Connectivity](https://www.algorist.com/problems/Edge_and_Vertex_Connectivity.html) | a graph, optionally two vertices | the fewest edges or vertices you can remove to break it apart |
| [Network Flow](https://www.algorist.com/problems/Network_Flow.html) | a graph with capacities, a source and a sink | the most that can be pushed from source to sink |
| [Drawing Graphs Nicely](https://www.algorist.com/problems/Drawing_Graphs_Nicely.html) | a graph | a drawing that shows its structure |
| [Drawing Trees](https://www.algorist.com/problems/Drawing_Trees.html) | a tree | a drawing of it |
| [Planarity Detection and Embedding](https://www.algorist.com/problems/Planarity_Detection_and_Embedding.html) | a graph | whether it can be drawn with no edges crossing, and such a drawing |

## Graph: Hard Problems

| Problem | In | Out |
|---|---|---|
| [Clique](https://www.algorist.com/problems/Clique.html) | a graph | the largest set of vertices all joined to each other |
| [Independent Set](https://www.algorist.com/problems/Independent_Set.html) | a graph | the largest set of vertices with no edge between any two |
| [Vertex Cover](https://www.algorist.com/problems/Vertex_Cover.html) | a graph | the smallest set of vertices touching every edge |
| [Traveling Salesman Problem](https://www.algorist.com/problems/Traveling_Salesman_Problem.html) | a weighted graph | the cheapest cycle through every vertex exactly once |
| [Hamiltonian Cycle](https://www.algorist.com/problems/Hamiltonian_Cycle.html) | a graph | an order visiting every vertex exactly once |
| [Graph Partition](https://www.algorist.com/problems/Graph_Partition.html) | a weighted graph, a size bound and a cost bound | a split into parts no bigger than the size bound, cutting no more than the cost bound |
| [Vertex Coloring](https://www.algorist.com/problems/Vertex_Coloring.html) | a graph | a coloring of the vertices using the fewest colors, so that no two neighbors match |
| [Edge Coloring](https://www.algorist.com/problems/Edge_Coloring.html) | a graph | the fewest colors for the edges so that edges meeting at a vertex differ |
| [Graph Isomorphism](https://www.algorist.com/problems/Graph_Isomorphism.html) | two graphs | a relabeling that turns one graph into the other, if such a relabeling exists |
| [Steiner Tree](https://www.algorist.com/problems/Steiner_Tree.html) | a graph and a subset of its vertices | the smallest tree connecting that subset |
| [Feedback Edge/Vertex Set](https://www.algorist.com/problems/Feedback_Edge_Vertex_Set.html) | a directed graph | the fewest edges or vertices to remove so that no cycle is left |

## Computational Geometry

| Problem | In | Out |
|---|---|---|
| [Robust Geometric Primitives](https://www.algorist.com/problems/Robust_Geometric_Primitives.html) | a point and a segment, or two segments | which side the point is on, or whether the segments cross — without rounding errors giving a wrong answer |
| [Convex Hull](https://www.algorist.com/problems/Convex_Hull.html) | n points | the smallest convex polygon holding them all |
| [Triangulation](https://www.algorist.com/problems/Triangulation.html) | a point set or a polyhedron | its interior cut into triangles |
| [Voronoi Diagrams](https://www.algorist.com/problems/Voronoi_Diagrams.html) | n points | the region around each point closer to it than to any other |
| [Nearest Neighbor Search](https://www.algorist.com/problems/Nearest_Neighbor_Search.html) | n points and a query point | the closest one |
| [Range Search](https://www.algorist.com/problems/Range_Search.html) | n points and a query polygon | the points falling inside it |
| [Point Location](https://www.algorist.com/problems/Point_Location.html) | a plane cut into regions, and a query point | the region it falls in |
| [Intersection Detection](https://www.algorist.com/problems/Intersection_Detection.html) | segments, or two polygons | which pairs cross, or the shape they share |
| [Bin Packing](https://www.algorist.com/problems/Bin_Packing.html) | items with sizes, bins with capacities | a packing using as few bins as possible |
| [Medial-Axis Transform](https://www.algorist.com/problems/Medial-Axis_Transform.html) | a polygon | the points inside that have more than one nearest point on the boundary — its skeleton |
| [Polygon Partitioning](https://www.algorist.com/problems/Polygon_Partitioning.html) | a polygon | a cut into as few simple pieces as possible, usually convex ones |
| [Simplifying Polygons](https://www.algorist.com/problems/Simplifying_Polygons.html) | a polygon with n vertices | one with fewer vertices that still looks like it |
| [Shape Similarity](https://www.algorist.com/problems/Shape_Similarity.html) | two shapes | how alike they are |
| [Motion Planning](https://www.algorist.com/problems/Motion_Planning.html) | a robot, a room with obstacles, a start and an end | the shortest path that gets the robot across without hitting anything |
| [Maintaining Line Arrangements](https://www.algorist.com/problems/Maintaining_Line_Arrangements.html) | n lines and segments | the cells, edges and vertices they cut the plane into |
| [Minkowski Sum](https://www.algorist.com/problems/Minkowski_Sum.html) | two point sets or polygons | every sum of a point from one and a point from the other |

## Set and String Problems

| Problem | In | Out |
|---|---|---|
| [Set Cover](https://www.algorist.com/problems/Set_Cover.html) | subsets of a universe | the fewest of them whose union is the whole universe |
| [Set Packing](https://www.algorist.com/problems/Set_Packing.html) | subsets of a universe | the most of them that share no element |
| [String Matching](https://www.algorist.com/problems/String_Matching.html) | a text and a pattern | where the pattern occurs |
| [Approximate String Matching](https://www.algorist.com/problems/Approximate_String_Matching.html) | a text, a pattern, and an edit budget | whether the pattern appears somewhere after that many edits or fewer |
| [Text Compression](https://www.algorist.com/problems/Text_Compression.html) | a string | a shorter string the original can be rebuilt from |
| [Cryptography](https://www.algorist.com/problems/Cryptography.html) | a message and a key | the encrypted text, or the message back |
| [Finite State Machine Minimization](https://www.algorist.com/problems/Finite_State_Machine_Minimization.html) | a deterministic finite state machine | the smallest one that behaves the same way |
| [Longest Common Substring/Subsequence](https://www.algorist.com/problems/Longest_Common_Substring.html) | a set of strings | the longest run of characters appearing, in order, in all of them |
| [Shortest Common Superstring](https://www.algorist.com/problems/Shortest_Common_Superstring.html) | a set of strings | the shortest string containing every one of them |
