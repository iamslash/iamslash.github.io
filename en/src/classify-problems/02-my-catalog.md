# There Are 55 Coding Interview Problems

In [There Are 75 Famous Problems](./01-skiena-catalog.md) we saw Skiena write
an Input and an Output for every problem. No algorithm name appears, so you
can find an entry knowing only what you have and what you want.

You cannot use those 75 for a coding interview as they are. `Voronoi Diagrams`
and `Medial-Axis Transform` do not come up in interviews. Different problems
do.

So **I built the list for interviews the same way.** I went back through about
3,000 problems I had solved on LeetCode.

## 1. In and Out Alone Do Not Tell Them Apart

At first I followed Skiena exactly and wrote only the two fields. Then this
happened.

```
  Largest run                      the contiguous run with the largest sum
                                   array -> one number
  Longest increasing subsequence   the longest increasing subsequence
                                   array -> one number
```

**You cannot tell them apart.** Contiguous or skipping is what decides the
method, and it does not show up in In or Out. So I added one more field.

```
  In                    what goes in
  Out                   what comes out
  Splitting question    In and Out are the same, but the method changes here
```

Those two split right here — **does it have to be contiguous?**

```
  yes   Largest run
  no    Longest increasing subsequence
```

The third field is the one you actually use. Read the problem, and **if you
can answer the splitting question**, the method is settled.

## 2. Nine Categories, 55 Problems

```
  Skiena      categories 7    problems 75      all of computer science
  this list   categories 9    problems 55      what shows up in interviews
```

There is no reason behind the number 55. **It is a starting point.** All I
fixed were the rules for growing and shrinking it.

```
  split    when the difference changes the method or the "why is this correct"
  merge    when two entries produce the same reasoning
  add      when you keep getting something wrong in review and no entry covers it
```

### Arrays and Ranges

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Window over a sequence | numbers or letters in a row, and one condition | the shortest or longest run that satisfies the condition | does the condition change monotonically as you widen and shrink the window. if the condition is about a sum, one negative number breaks it | [Longest Substring Without Repeating Characters](https://github.com/iamslash/learntocode/blob/master/leetcode/LongestSubstringWithoutRepeatingCharacters/MainApp.java) · [Minimum Size Subarray Sum](https://github.com/iamslash/learntocode/tree/master/leetcode/MinimumSizeSubarraySum) |
| Largest run | numbers in a row | the run with the largest sum or product | it must be contiguous. picking non-adjacent items is a different problem | [Maximum Subarray](https://github.com/iamslash/learntocode/blob/master/leetcode/MaximumSubarray/MainApp.java) · [Maximum Product Subarray](https://github.com/iamslash/learntocode/blob/master/leetcode/MaximumProductSubarray/Solution.java) |
| Longest increasing subsequence | numbers or items in a row | the length of the longest subsequence that only goes up | must it be contiguous. if you may skip, keep only the tail values and binary search | [Longest Increasing Subsequence](https://github.com/iamslash/learntocode/blob/master/leetcode/LongestIncreasingSubsequence/Solution.java) · [Russian Doll Envelopes](https://github.com/iamslash/learntocode/tree/master/leetcode2/RussianDollEnvelopes) |
| Next greater element | numbers in a row | for each position, the first larger or smaller value it meets, or the range those values define | if an earlier element is smaller than the current one, is it useless forever | [Daily Temperatures](https://github.com/iamslash/learntocode/blob/master/leetcode/DailyTemperatures/Solution.java) · [Largest Rectangle in Histogram](https://github.com/iamslash/learntocode/tree/master/leetcode/LargestRectangleinHistogram) |
| Prefix and range | a sequence or a matrix, plus repeated range questions | the sum or minimum of each range | do values change in between. if not, prefix sums; if so, a tree | [Range Sum Query - Immutable](https://github.com/iamslash/learntocode/tree/master/leetcode/RangeSumQuery-Immutable) · [Range Sum Query 2D - Mutable](https://github.com/iamslash/learntocode/tree/master/leetcode/RangeSumQuery2D-Mutable) |
| Kth element | unsorted values and k | the kth largest or smallest value | do you need just the kth one, or all k of them | [Kth Largest Element in an Array](https://github.com/iamslash/learntocode/blob/master/leetcode/KthLargestElementinanArray/MainApp.java) · [Top K Frequent Elements](https://github.com/iamslash/learntocode/blob/master/leetcode/TopKFrequentElements/MainApp.java) |
| Count and tally | values | how many times, is there a majority, which value is missing | is the range of values narrow. if it is, counting alone is enough | [Majority Element](https://github.com/iamslash/learntocode/tree/master/leetcode/MajorityElement) · [First Missing Positive](https://github.com/iamslash/learntocode/tree/master/leetcode/FirstMissingPositive) |
| Pair with target | numbers and a target | the two or three that sum to the target | may you sort. if yes, two ends; if no, a hash | [Two Sum](https://github.com/iamslash/learntocode/blob/master/leetcode/TwoSum/MainApp.java) · [3Sum](https://github.com/iamslash/learntocode/blob/master/leetcode/3sum/MainApp.java) |

### Order and Priority

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Boundary by monotonicity | something sorted or monotone, and a true/false test | the point where the test first turns true | is the answer itself monotone. then binary search on the value | [Search in Rotated Sorted Array](https://github.com/iamslash/learntocode/tree/master/leetcode/SearchinRotatedSortedArray) · [Koko Eating Bananas](https://github.com/iamslash/learntocode/tree/master/leetcode/KokoEatingBananas) |
| Two ends moving in | a row that is sorted, or that you may sort | a pair, an area, or a count you get by closing in from both ends | do you close in from both ends, or fix one side and close in | [Two Sum II - Input Array Is Sorted](https://github.com/iamslash/learntocode/tree/master/leetcode/TwoSumII-Inputarrayissorted) · [Valid Triangle Number](https://github.com/iamslash/learntocode/tree/master/leetcode/ValidTriangleNumber) |
| Intervals | intervals with a start and an end | merged, maximum overlap, or the most you can pick | sort by start or sort by end. it depends on what you want | [Merge Intervals](https://github.com/iamslash/learntocode/blob/master/leetcode/MergeIntervals/MainApp.java) · [Non-overlapping Intervals](https://github.com/iamslash/learntocode/tree/master/leetcode/Non-overlappingIntervals) |
| Pull the best one next | a situation where you must take the best or worst each time | the result after processing everything | do the candidates change after each pull. if not, just sort | [Merge k Sorted Lists](https://github.com/iamslash/learntocode/blob/master/leetcode/MergekSortedLists/MainApp.java) · [Meeting Rooms II](https://github.com/iamslash/learntocode/blob/master/leetcode/MeetingRoomsII/MainApp.java) |
| Sort then scan | items you must decide a sort order for | the answer you get from one sort and one pass | does fixing one criterion make the rest simple | [Largest Number](https://github.com/iamslash/learntocode/tree/master/leetcode/LargestNumber) · [Queue Reconstruction by Height](https://github.com/iamslash/learntocode/tree/master/leetcode/QueueReconstructionbyHeight) |

### Grids and Matrices

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Walk a grid | a grid and a starting cell | the cells you reach, the number of blobs, or the fewest steps | is there one start or many. with many you spread from all of them at once | [Number of Islands](https://github.com/iamslash/learntocode/blob/master/leetcode/NumberOfIslands/MainApp.java) · [Walls and Gates](https://github.com/iamslash/learntocode/tree/master/leetcode2/WallsandGates) |
| Transform in place | a matrix | rotated, transposed, or marked | must you use no extra space. then swap in layers | [Rotate Image](https://github.com/iamslash/learntocode/tree/master/leetcode/RotateImage) · [Set Matrix Zeroes](https://github.com/iamslash/learntocode/blob/master/leetcode/SetMatrixZeroes/MainApp.java) |
| Grid DP | a grid and a cost per cell | the best value from one corner to the opposite one | does it only move one way. if you can come back, first check there is no cycle | [Minimum Path Sum](https://github.com/iamslash/learntocode/tree/master/leetcode/MinimumPathSum) · [Longest Increasing Path in a Matrix](https://github.com/iamslash/learntocode/tree/master/leetcode/LongestIncreasingPathinaMatrix) |
| Search a sorted grid | a matrix sorted by row and column, and a value to find | is it there | is it still sorted if you flatten it into one row. if not, start from a corner | [Search a 2D Matrix](https://github.com/iamslash/learntocode/tree/master/leetcode/Searcha2DMatrix) · [Search a 2D Matrix II](https://github.com/iamslash/learntocode/blob/master/leetcode/Searcha2DMatrixII/MainApp.java) |
| Simulate on a grid | a grid and a rule that changes it | the next state, or the result of applying the rule until nothing changes | do the updates happen all at once or one after another | [Game of Life](https://github.com/iamslash/learntocode/tree/master/leetcode/GameOfLife) · [Candy Crush](https://github.com/iamslash/learntocode/blob/master/leetcode/CandyCrush/MainApp.java) |

### Strings

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Palindrome | a string | is it a palindrome, or the longest palindromic piece | do you expand from the middle or close in from both ends | [Longest Palindromic Substring](https://github.com/iamslash/learntocode/blob/master/leetcode/LongestPalindromicSubstring/MainApp.java) · [Valid Palindrome](https://github.com/iamslash/learntocode/blob/master/leetcode/ValidPalindrome/MainApp.java) |
| Brackets and expressions | a string with brackets or operators | is it valid, the computed value, or the expanded result | is there nesting. if yes, a stack; if no, counting alone | [Minimum Add to Make Parentheses Valid](https://github.com/iamslash/learntocode/tree/master/leetcode/MinimumAddtoMakeParenthesesValid) · [Basic Calculator](https://github.com/iamslash/learntocode/tree/master/leetcode2/BasicCalculator) |
| Edit distance | two strings | the fewest operations to turn one into the other | which operations are allowed. remove the replace operation and it becomes a different problem | [Edit Distance](https://github.com/iamslash/learntocode/tree/master/leetcode/EditDistance) · [Delete Operation for Two Strings](https://github.com/iamslash/learntocode/tree/master/leetcode/DeleteOperationforTwoStrings) |
| Common subsequence | two strings or two arrays | the longest thing contained in both | must it be contiguous. if you may skip, it is a subsequence | [Longest Common Subsequence](https://github.com/iamslash/learntocode/tree/master/leetcode/LongestCommonSubsequence) · [Maximum Length of Repeated Subarray](https://github.com/iamslash/learntocode/tree/master/leetcode/MaximumLengthofRepeatedSubarray) |
| Pattern in text | a long text and one or more pieces to find | where the pieces occur | is there more than one piece. with many, a trie or a hash | [Find All Anagrams in a String](https://github.com/iamslash/learntocode/blob/master/leetcode/FindAllAnagramsinaString/MainApp.java) · [Add Bold Tag in String](https://github.com/iamslash/learntocode/tree/master/leetcode/AddBoldTaginString) |
| Prefix set | several words | finding the words that share a prefix | are the queries repeated. for a single one a trie is not worth building | [Longest Common Prefix](https://github.com/iamslash/learntocode/tree/master/leetcode/LongestCommonPrefix) · [Word Search II](https://github.com/iamslash/learntocode/tree/master/leetcode2/WordSearchII) |
| Same letters | one string or several | are the letter counts the same, grouping the ones that match | are you only checking whether two match, or grouping all of them | [Valid Anagram](https://github.com/iamslash/learntocode/tree/master/leetcode/ValidAnagram) · [Group Anagrams](https://github.com/iamslash/learntocode/tree/master/leetcode/GroupAnagrams) |
| Rewrite a string | a string with a rule written in it | the result of applying the rule | does the rule finish in one pass, or apply again to what came out | [Decode String](https://github.com/iamslash/learntocode/blob/master/leetcode/DecodeString/MainApp.java) · [Count and Say](https://github.com/iamslash/learntocode/tree/master/leetcode/CountAndSay) |

### Trees

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Walk a tree | a tree | the visiting order, or a value gathered on the way | do you carry something down, or gather something up | [Path Sum](https://github.com/iamslash/learntocode/tree/master/leetcode/PathSum) · [Maximum Depth of Binary Tree](https://github.com/iamslash/learntocode/tree/master/leetcode/MaximumDepthOfBinaryTree) |
| Tree DP | a tree and a value per node | the best value collected from the subtrees below | is one value enough to send up from a child, or do you need several | [Binary Tree Maximum Path Sum](https://github.com/iamslash/learntocode/blob/master/leetcode/BinaryTreeMaximumPathSum/MainApp.java) · [House Robber III](https://github.com/iamslash/learntocode/tree/master/leetcode/HouseRobberIII) |
| Build a tree | traversal output or a serialized string | the original tree | where in the input is the root | [Construct Binary Tree from Preorder and Inorder Traversal](https://github.com/iamslash/learntocode/tree/master/leetcode/ConstructBinaryTreefromPreorderandInorderTraversal) · [Construct Binary Tree from Inorder and Postorder Traversal](https://github.com/iamslash/learntocode/tree/master/leetcode/ConstructBinaryTreefromInorderandPostorderTraversal) |
| Binary search tree | a tree with the sorted property | insert, delete, kth, or validate | do you build a tree from a sorted sequence, or pull a sorted sequence out of a tree | [Convert Sorted Array to Binary Search Tree](https://github.com/iamslash/learntocode/tree/master/leetcode/ConvertSortedArraytoBinarySearchTree) · [Kth Smallest Element in a BST](https://github.com/iamslash/learntocode/tree/master/leetcode/KthSmallestElementinaBST) |
| Lowest common ancestor | a tree and two nodes | their nearest common ancestor | can you use the sorted property. in a binary search tree one walk down from the root solves it | [Lowest Common Ancestor of a Binary Search Tree](https://github.com/iamslash/learntocode/blob/master/leetcode/LowestCommonAncestorofaBinarySearchTree/MainApp.java) · [Lowest Common Ancestor of a Binary Tree](https://github.com/iamslash/learntocode/blob/master/leetcode/LowestCommonAncestorofaBinaryTree/MainApp.java) |

### Graphs

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Connected components | vertices and edges, or a grid | how many blobs, are these two in the same blob, which edge closes a cycle | do the edges arrive all at once or one at a time | [Number of Connected Components in an Undirected Graph](https://github.com/iamslash/learntocode/tree/master/leetcode/NumberofConnectedComponentsinanUndirectedGraph) · [Redundant Connection](https://github.com/iamslash/learntocode/tree/master/leetcode/RedundantConnection) |
| Topological order | tasks with precedence | an execution order, or whether such an order exists at all | with a cycle there is no answer. checking for one is half the problem | [Course Schedule](https://github.com/iamslash/learntocode/blob/master/leetcode/CourseSchedule/MainApp.java) · [Course Schedule II](https://github.com/iamslash/learntocode/tree/master/leetcode/CourseScheduleII) |
| Shortest path | a graph and a start, plus a target if needed | the least cost or the fewest steps | are all weights 1, are any negative. the method splits three ways | [Word Ladder](https://github.com/iamslash/learntocode/blob/master/leetcode2/WordLadder/MainApp.java) · [Network Delay Time](https://github.com/iamslash/learntocode/blob/master/leetcode/NetworkDelayTime/MainApp.java) |
| Cycle | a graph or a linked list | is there a cycle, where does it start, which parts never reach a cycle | is there one next, or several branches. with branches you need a separate in-progress mark | [Linked List Cycle II](https://github.com/iamslash/learntocode/tree/master/leetcode/LinkedListCycleII) · [Find Eventual Safe States](https://github.com/iamslash/learntocode/tree/master/leetcode/FindEventualSafeStates) |
| Spanning and flow | a graph with weights or capacities | the cheapest way to connect everything, the most you can push through, the largest matching | does it split into two sides. if it does, it becomes a matching problem | [Min Cost to Connect All Points](https://github.com/iamslash/learntocode/blob/master/leetcode2/MinCosttoConnectAllPoints/MainApp.java) · [Maximum Number of Accepted Invitations](https://github.com/iamslash/learntocode/blob/master/leetcode2/MaximumNumberofAcceptedInvitations/MainApp.java) |

### States and Choices

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Carry state forward | a few states to choose from at each step | the best value at the last step | do you know the number of states in advance, or does it grow with the input | [Best Time to Buy and Sell Stock](https://github.com/iamslash/learntocode/blob/master/leetcode/BestTimetoBuyandSellStock/MainApp.java) · [Best Time to Buy and Sell Stock IV](https://github.com/iamslash/learntocode/tree/master/leetcode/BestTimetoBuyandSellStockIV) |
| Count the ways | a grid or steps, plus constraints | how many ways reach the end | are the places you can go fixed from the start, or do you have to read the input | [Unique Paths](https://github.com/iamslash/learntocode/blob/master/leetcode/UniquePaths/MainApp.java) · [Decode Ways](https://github.com/iamslash/learntocode/blob/master/leetcode/DecodeWays/MainApp.java) |
| Interval DP | a row, and an operation that works on intervals | the best cost of merging the whole thing | does it split on what you do last | [Burst Balloons](https://github.com/iamslash/learntocode/tree/master/leetcode/BurstBalloons) · [Strange Printer](https://github.com/iamslash/learntocode/tree/master/leetcode2/StrangePrinter) |
| Knapsack | items with a size and a value, and a limit | the best value chosen against a limit or a target | do you use the same item more than once. if so the loop runs the other way | [Ones and Zeroes](https://github.com/iamslash/learntocode/tree/master/leetcode/OnesandZeroes) · [Coin Change](https://github.com/iamslash/learntocode/blob/master/leetcode/CoinChange/MainApp.java) |
| List every arrangement | a small n and constraints | every arrangement that satisfies the constraints | can you prune. if not there are too many answers | [Letter Combinations of a Phone Number](https://github.com/iamslash/learntocode/blob/master/leetcode/LetterCombinationsofaPhoneNumber/MainApp.java) · [Generate Parentheses](https://github.com/iamslash/learntocode/blob/master/leetcode/GenerateParentheses/Solution.java) |
| Small n, every subset | n around 20, a different value per subset | the best value after trying everything | is the subset enough to describe the state, or must you also track where you are | [Can I Win](https://github.com/iamslash/learntocode/tree/master/leetcode/CanIWin) · [Android Unlock Patterns](https://github.com/iamslash/learntocode/tree/master/leetcode/AndroidUnlockPatterns) |
| Win or lose | a game with alternating moves | does the first player win | does the board split into independent piles. if it does, Grundy numbers | [Nim Game](https://github.com/iamslash/learntocode/tree/master/leetcode/NimGame) · [Flip Game II](https://github.com/iamslash/learntocode/tree/master/leetcode/FlipGameII) |

### Numbers

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Digits and bases | one number, or a number written as a string | digits handled, or the base changed | does it go past the type range. if so, treat it as a string | [Reverse Integer](https://github.com/iamslash/learntocode/tree/master/leetcode/ReverseInteger) · [Excel Sheet Column Title](https://github.com/iamslash/learntocode/tree/master/leetcode/ExcelSheetColumnTitle) |
| Divisors and primes | one number or a range | is it prime, how many primes, what are the divisors | do you look at one number or at a range. for a range, build a sieve | [Prime Palindrome](https://github.com/iamslash/learntocode/tree/master/leetcode/PrimePalindrome) · [Count Primes](https://github.com/iamslash/learntocode/tree/master/leetcode/CountPrimes) |
| Bit tricks | numbers | a value you get with bit operations | how many of each are paired up. with two, one XOR solves it | [Single Number](https://github.com/iamslash/learntocode/blob/master/leetcode/SingleNumber/MainApp.java) · [Single Number II](https://github.com/iamslash/learntocode/tree/master/leetcode/SingleNumberII) |
| Combinatorics | n and a modulus, plus k if needed | the number of cases | is there a division. if so you need an inverse | [Count All Valid Pickup and Delivery Options](https://github.com/iamslash/learntocode/tree/master/leetcode2/CountAllValidPickupandDeliveryOptions) · [Number of Ways to Reorder Array to Get Same BST](https://github.com/iamslash/learntocode/tree/master/leetcode2/NumberofWaystoReorderArraytoGetSameBST) |
| Chance and sampling | a situation that needs randomness | a result where every choice is equally likely | do you know the total size in advance. if not, pick as the items go past | [Shuffle an Array](https://github.com/iamslash/learntocode/tree/master/leetcode/ShuffleanArray) · [Linked List Random Node](https://github.com/iamslash/learntocode/tree/master/leetcode/LinkedListRandomNode) |
| Geometry | points or shapes | distance, containment, or the enclosing shape | do you use floats. if so, rounding error is half the problem | [Max Points on a Line](https://github.com/iamslash/learntocode/tree/master/leetcode/MaxPointsonaLine) · [Generate Random Point in a Circle](https://github.com/iamslash/learntocode/tree/master/leetcode/GenerateRandomPointinaCircle) |

### Data Structures

| Problem | In | Out | Splitting question | Examples |
|---|---|---|---|---|
| Design a structure | a list of operations and a time limit | a structure where all of them are fast | do you do the work on the way in, or on the way out | [Two Sum III - Data structure design](https://github.com/iamslash/learntocode/tree/master/leetcode/TwoSumIII-Datastructuredesign) · [Design Twitter](https://github.com/iamslash/learntocode/blob/master/leetcode/DesignTwitter/Solution.java) |
| Cache and eviction | a capacity limit and an access log | a structure that decides what to keep and what to drop | is the eviction rule time or count | [LRU Cache](https://github.com/iamslash/learntocode/blob/master/leetcode/LRUCache/MainApp.java) · [LFU Cache](https://github.com/iamslash/learntocode/blob/master/leetcode2/LFUCache/MainApp.java) |
| Stack and queue discipline | a rule where you push and pop at one end only | a structure that answers extra queries while keeping that rule | do they also ask for something like the minimum | [Min Stack](https://github.com/iamslash/learntocode/blob/master/leetcode/MinStack/Solution.java) · [Implement Stack using Queues](https://github.com/iamslash/learntocode/blob/master/leetcode/ImplementStackusingQueues/MainApp.java) |
| Key to value | keys and values, and the operations required | a structure where insert, delete and lookup are all constant time | is there also a random pick. if so, keep an array alongside | [Design HashMap](https://github.com/iamslash/learntocode/blob/master/leetcode/DesignHashMap/MyHashMap.20200714.java) · [Insert Delete GetRandom O(1) - Duplicates allowed](https://github.com/iamslash/learntocode/tree/master/leetcode2/InsertDeleteGetRandomO%281%29-Duplicatesallowed) |
| Iterate on demand | nested or compressed data | an iterator that hands them over one at a time | may you expand everything in advance. if not, make it lazy | [Flatten Nested List Iterator](https://github.com/iamslash/learntocode/tree/master/leetcode/FlattenNestedListIterator) · [Binary Search Tree Iterator](https://github.com/iamslash/learntocode/blob/master/leetcode/BinarySearchTreeIterator/MainApp.java) |
| Linked list surgery | a chain of nodes | reverse, cut, merge, find a cycle | do you know the length in advance. if not, use two pointers | [Remove Nth Node From End of List](https://github.com/iamslash/learntocode/tree/master/leetcode/RemoveNthNodeFromEndofList) · [Reverse Linked List II](https://github.com/iamslash/learntocode/tree/master/leetcode/ReverseLinkedListII) |

## 3. How To Use It

Cover the right-hand side and look at the three fields on the left. When you
read a problem and **can answer the splitting question**, that problem is
solved. When no answer comes, that is what you need to study again.
