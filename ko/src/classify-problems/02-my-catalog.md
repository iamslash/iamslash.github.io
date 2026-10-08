# 코딩 인터뷰 문제는 55개입니다

[유명한 문제는 75개입니다](./01-skiena-catalog.md) 에서 Skiena 가 문제마다
Input, Output 을 적어둔 걸 봤습니다. 알고리즘 이름이 없어서, 손에 든 것과
원하는 것만 알면 찾아집니다.

그 75개를 코딩 인터뷰에 그대로 쓰기는 어렵습니다. `Voronoi Diagrams` 나
`Medial-Axis Transform` 은 면접에 안 나옵니다. 나오는 문제가 다릅니다.

그래서 **같은 방식으로 면접 쪽 목록을 만들었습니다.** LeetCode 에서 풀어본 약
3,000 문제를 다시 추렸습니다.

## 1. In/Out 만으로는 안 갈립니다

처음에는 Skiena 를 그대로 따라 In/Out 두 칸만 적었습니다. 그런데 이런 일이
생깁니다.

```
  Largest run                      합이 가장 큰 연속 구간      배열 → 수 하나
  Longest increasing subsequence   가장 긴 늘어나는 부분수열   배열 → 수 하나
```

**둘이 구별이 안 됩니다.** 연속이냐 띄엄띄엄이냐가 방법을 가르는데 In/Out 에는
안 나옵니다. 그래서 칸을 하나 더 뒀습니다.

```
  In             들어가는 것
  Out            나오는 것
  가르는 조건     In, Out 은 같은데 방법이 달라지는 지점
```

방금 둘은 여기서 갈립니다 — **연속이어야 하나?**

```
  예        Largest run
  아니오     Longest increasing subsequence
```

세 번째 칸이 실제로 쓰는 칸입니다. 지문을 읽고 **여기에 답할 수 있으면** 방법이
정해집니다.

## 2. 범주 9, 문제 55

```
  Skiena      범주  7    문제 75      전산학 전체
  이 목록     범주  9    문제 55      면접에 나오는 것
```

55라는 수에 근거는 없습니다. **출발점입니다.** 늘리고 줄이는 규칙만 정해뒀습니다.

```
  쪼갠다    그 구분이 방법이나 "왜 맞는가" 를 바꿀 때
  합친다    두 칸이 같은 추론을 낳을 때
  더한다    복습하다 반복해서 걸리는데 지금 칸으로 표현이 안 될 때
```


### Arrays and Ranges

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Window over a sequence | 한 줄로 늘어선 수나 글자, 조건 하나 | 조건을 만족하는 가장 짧은 또는 긴 연속 구간 | 창을 넓히고 줄일 때 조건이 단조로 변하나. 합을 보는 조건이면 음수가 섞인 순간 깨진다 | [Longest Substring Without Repeating Characters](https://github.com/iamslash/learntocode/blob/master/leetcode/LongestSubstringWithoutRepeatingCharacters/MainApp.java) · [Minimum Size Subarray Sum](https://github.com/iamslash/learntocode/tree/master/leetcode/MinimumSizeSubarraySum) |
| Largest run | 한 줄로 늘어선 수 | 합이나 곱이 가장 큰 연속 구간 | 연속이어야 한다. 띄엄띄엄 고르면 다른 문제다 | [Maximum Subarray](https://github.com/iamslash/learntocode/blob/master/leetcode/MaximumSubarray/MainApp.java) · [Maximum Product Subarray](https://github.com/iamslash/learntocode/blob/master/leetcode/MaximumProductSubarray/Solution.java) |
| Longest increasing subsequence | 한 줄로 늘어선 수나 항목 | 늘어나기만 하는 가장 긴 부분수열의 길이 | 연속이어야 하나. 띄엄띄엄 골라도 되면 끝값만 들고 이분탐색한다 | [Longest Increasing Subsequence](https://github.com/iamslash/learntocode/blob/master/leetcode/LongestIncreasingSubsequence/Solution.java) · [Russian Doll Envelopes](https://github.com/iamslash/learntocode/tree/master/leetcode2/RussianDollEnvelopes) |
| Next greater element | 한 줄로 늘어선 수 | 각 자리에서 처음 만나는 더 크거나 작은 값, 또는 그렇게 정해지는 구간 | 지금 원소보다 작은 과거는 영원히 쓸모없나 | [Daily Temperatures](https://github.com/iamslash/learntocode/blob/master/leetcode/DailyTemperatures/Solution.java) · [Largest Rectangle in Histogram](https://github.com/iamslash/learntocode/tree/master/leetcode/LargestRectangleinHistogram) |
| Prefix and range | 수열이나 행렬, 그리고 반복되는 구간 질문 | 각 구간의 합이나 최소 | 중간에 값이 바뀌나. 안 바뀌면 누적합, 바뀌면 트리 | [Range Sum Query - Immutable](https://github.com/iamslash/learntocode/tree/master/leetcode/RangeSumQuery-Immutable) · [Range Sum Query 2D - Mutable](https://github.com/iamslash/learntocode/tree/master/leetcode/RangeSumQuery2D-Mutable) |
| Kth element | 정렬되지 않은 값들과 k | k번째로 크거나 작은 값 | k번째 하나만 필요한가, k개 전부가 필요한가 | [Kth Largest Element in an Array](https://github.com/iamslash/learntocode/blob/master/leetcode/KthLargestElementinanArray/MainApp.java) · [Top K Frequent Elements](https://github.com/iamslash/learntocode/blob/master/leetcode/TopKFrequentElements/MainApp.java) |
| Count and tally | 값들 | 몇 번 나왔나, 과반이 있나, 빠진 값이 무엇인가 | 값의 범위가 좁나. 좁으면 세기만 해도 된다 | [Majority Element](https://github.com/iamslash/learntocode/tree/master/leetcode/MajorityElement) · [First Missing Positive](https://github.com/iamslash/learntocode/tree/master/leetcode/FirstMissingPositive) |
| Pair with target | 수들과 목표값 | 합이 목표가 되는 둘 또는 셋 | 정렬해도 되나. 되면 양끝, 안 되면 해시 | [Two Sum](https://github.com/iamslash/learntocode/blob/master/leetcode/TwoSum/MainApp.java) · [3Sum](https://github.com/iamslash/learntocode/blob/master/leetcode/3sum/MainApp.java) |

### Order and Priority

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Boundary by monotonicity | 정렬됐거나 단조인 것, 참거짓을 가리는 조건 | 조건이 처음 참이 되는 지점 | 답 자체가 단조인가. 그러면 값을 이분탐색한다 | [Search in Rotated Sorted Array](https://github.com/iamslash/learntocode/tree/master/leetcode/SearchinRotatedSortedArray) · [Koko Eating Bananas](https://github.com/iamslash/learntocode/tree/master/leetcode/KokoEatingBananas) |
| Two ends moving in | 정렬됐거나 정렬해도 되는 한 줄 | 양 끝에서 좁혀 얻는 짝, 넓이, 또는 개수 | 양끝에서 좁히나, 한쪽을 고정하고 좁히나 | [Two Sum II - Input Array Is Sorted](https://github.com/iamslash/learntocode/tree/master/leetcode/TwoSumII-Inputarrayissorted) · [Valid Triangle Number](https://github.com/iamslash/learntocode/tree/master/leetcode/ValidTriangleNumber) |
| Intervals | 시작과 끝이 있는 구간들 | 병합, 최대 겹침, 또는 고를 수 있는 최대 개수 | 시작으로 정렬하나 끝으로 정렬하나. 목적에 따라 갈린다 | [Merge Intervals](https://github.com/iamslash/learntocode/blob/master/leetcode/MergeIntervals/MainApp.java) · [Non-overlapping Intervals](https://github.com/iamslash/learntocode/tree/master/leetcode/Non-overlappingIntervals) |
| Pull the best one next | 매번 가장 좋거나 나쁜 것을 꺼내야 하는 상황 | 전부 처리하고 난 결과 | 꺼낼 때마다 후보가 바뀌나. 안 바뀌면 그냥 정렬 | [Merge k Sorted Lists](https://github.com/iamslash/learntocode/blob/master/leetcode/MergekSortedLists/MainApp.java) · [Meeting Rooms II](https://github.com/iamslash/learntocode/blob/master/leetcode/MeetingRoomsII/MainApp.java) |
| Sort then scan | 정렬 기준을 정해야 하는 항목들 | 한 기준으로 정렬한 뒤 한 번 훑어 얻는 답 | 한 기준을 고정하면 나머지가 단순해지나 | [Largest Number](https://github.com/iamslash/learntocode/tree/master/leetcode/LargestNumber) · [Queue Reconstruction by Height](https://github.com/iamslash/learntocode/tree/master/leetcode/QueueReconstructionbyHeight) |

### Grids and Matrices

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Walk a grid | 격자와 시작점 | 닿는 칸, 덩어리 수, 또는 최소 걸음 | 시작점이 하나인가 여럿인가. 여럿이면 동시에 퍼뜨린다 | [Number of Islands](https://github.com/iamslash/learntocode/blob/master/leetcode/NumberOfIslands/MainApp.java) · [Walls and Gates](https://github.com/iamslash/learntocode/tree/master/leetcode2/WallsandGates) |
| Transform in place | 행렬 | 회전, 전치, 또는 표시한 결과 | 추가 공간을 못 쓰나. 그러면 겹겹이 맞바꾼다 | [Rotate Image](https://github.com/iamslash/learntocode/tree/master/leetcode/RotateImage) · [Set Matrix Zeroes](https://github.com/iamslash/learntocode/blob/master/leetcode/SetMatrixZeroes/MainApp.java) |
| Grid DP | 격자와 칸마다의 비용 | 한 귀퉁이에서 반대편까지의 최적값 | 한 방향으로만 가나. 되돌아올 수 있으면 사이클이 없는지부터 본다 | [Minimum Path Sum](https://github.com/iamslash/learntocode/tree/master/leetcode/MinimumPathSum) · [Longest Increasing Path in a Matrix](https://github.com/iamslash/learntocode/tree/master/leetcode/LongestIncreasingPathinaMatrix) |
| Search a sorted grid | 행과 열이 정렬된 행렬과 찾을 값 | 있나 | 한 줄로 펴도 정렬인가. 아니면 모서리에서 시작한다 | [Search a 2D Matrix](https://github.com/iamslash/learntocode/tree/master/leetcode/Searcha2DMatrix) · [Search a 2D Matrix II](https://github.com/iamslash/learntocode/blob/master/leetcode/Searcha2DMatrixII/MainApp.java) |
| Simulate on a grid | 격자와 바뀌는 규칙 | 규칙을 적용한 다음 상태, 또는 변하지 않을 때까지 적용한 결과 | 갱신이 동시에 일어나나 차례로 일어나나 | [Game of Life](https://github.com/iamslash/learntocode/tree/master/leetcode/GameOfLife) · [Candy Crush](https://github.com/iamslash/learntocode/blob/master/leetcode/CandyCrush/MainApp.java) |

### Strings

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Palindrome | 문자열 | 회문인가, 또는 회문인 가장 긴 조각 | 가운데에서 퍼지나, 양끝에서 좁히나 | [Longest Palindromic Substring](https://github.com/iamslash/learntocode/blob/master/leetcode/LongestPalindromicSubstring/MainApp.java) · [Valid Palindrome](https://github.com/iamslash/learntocode/blob/master/leetcode/ValidPalindrome/MainApp.java) |
| Brackets and expressions | 괄호나 연산자가 섞인 문자열 | 유효한가, 계산 결과, 또는 펼친 결과 | 중첩이 있나. 있으면 스택, 없으면 세기만 | [Minimum Add to Make Parentheses Valid](https://github.com/iamslash/learntocode/tree/master/leetcode/MinimumAddtoMakeParenthesesValid) · [Basic Calculator](https://github.com/iamslash/learntocode/tree/master/leetcode2/BasicCalculator) |
| Edit distance | 문자열 둘 | 하나를 다른 하나로 바꾸는 최소 연산 수 | 허용되는 연산이 무엇인가. 교체가 빠지면 다른 문제다 | [Edit Distance](https://github.com/iamslash/learntocode/tree/master/leetcode/EditDistance) · [Delete Operation for Two Strings](https://github.com/iamslash/learntocode/tree/master/leetcode/DeleteOperationforTwoStrings) |
| Common subsequence | 문자열이나 배열 둘 | 둘 다에 들어 있는 가장 긴 것 | 연속이어야 하나. 띄엄띄엄 되면 부분수열 | [Longest Common Subsequence](https://github.com/iamslash/learntocode/tree/master/leetcode/LongestCommonSubsequence) · [Maximum Length of Repeated Subarray](https://github.com/iamslash/learntocode/tree/master/leetcode/MaximumLengthofRepeatedSubarray) |
| Pattern in text | 긴 글과 찾을 조각 하나 또는 여럿 | 조각이 어디에 나오나 | 조각이 여럿인가. 여럿이면 트라이나 해시 | [Find All Anagrams in a String](https://github.com/iamslash/learntocode/blob/master/leetcode/FindAllAnagramsinaString/MainApp.java) · [Add Bold Tag in String](https://github.com/iamslash/learntocode/tree/master/leetcode/AddBoldTaginString) |
| Prefix set | 단어 여러 개 | 접두사를 공유하는 단어 찾기 | 질의가 반복되나. 한 번이면 트라이를 지을 값이 없다 | [Longest Common Prefix](https://github.com/iamslash/learntocode/tree/master/leetcode/LongestCommonPrefix) · [Word Search II](https://github.com/iamslash/learntocode/tree/master/leetcode2/WordSearchII) |
| Same letters | 문자열 하나 또는 여럿 | 글자 구성이 같은가, 같은 것끼리 묶기 | 같은지만 보나, 같은 것끼리 묶나 | [Valid Anagram](https://github.com/iamslash/learntocode/tree/master/leetcode/ValidAnagram) · [Group Anagrams](https://github.com/iamslash/learntocode/tree/master/leetcode/GroupAnagrams) |
| Rewrite a string | 규칙이 적힌 문자열 | 규칙대로 고쳐 쓴 결과 | 규칙이 한 번에 끝나나, 나온 결과에 또 적용되나 | [Decode String](https://github.com/iamslash/learntocode/blob/master/leetcode/DecodeString/MainApp.java) · [Count and Say](https://github.com/iamslash/learntocode/tree/master/leetcode/CountAndSay) |

### Trees

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Walk a tree | 트리 | 방문 순서, 또는 훑으면서 모은 값 | 위에서 아래로 가져가나, 아래에서 위로 모으나 | [Path Sum](https://github.com/iamslash/learntocode/tree/master/leetcode/PathSum) · [Maximum Depth of Binary Tree](https://github.com/iamslash/learntocode/tree/master/leetcode/MaximumDepthOfBinaryTree) |
| Tree DP | 트리와 노드마다의 값 | 부분 트리에서 올려 모은 최적값 | 자식이 올려보낼 값이 하나면 되나, 여럿이어야 하나 | [Binary Tree Maximum Path Sum](https://github.com/iamslash/learntocode/blob/master/leetcode/BinaryTreeMaximumPathSum/MainApp.java) · [House Robber III](https://github.com/iamslash/learntocode/tree/master/leetcode/HouseRobberIII) |
| Build a tree | 순회 결과나 직렬화된 문자열 | 원래 트리 | 뿌리를 어디서 알 수 있나 | [Construct Binary Tree from Preorder and Inorder Traversal](https://github.com/iamslash/learntocode/tree/master/leetcode/ConstructBinaryTreefromPreorderandInorderTraversal) · [Construct Binary Tree from Inorder and Postorder Traversal](https://github.com/iamslash/learntocode/tree/master/leetcode/ConstructBinaryTreefromInorderandPostorderTraversal) |
| Binary search tree | 정렬 성질이 있는 트리 | 삽입, 삭제, k번째, 또는 검증 | 정렬된 수열에서 트리를 만드나, 트리에서 정렬된 수열을 꺼내나 | [Convert Sorted Array to Binary Search Tree](https://github.com/iamslash/learntocode/tree/master/leetcode/ConvertSortedArraytoBinarySearchTree) · [Kth Smallest Element in a BST](https://github.com/iamslash/learntocode/tree/master/leetcode/KthSmallestElementinaBST) |
| Lowest common ancestor | 트리와 두 노드 | 둘의 가장 가까운 공통 조상 | 정렬 성질을 쓸 수 있나. BST 면 뿌리에서 한 번 내려가면 끝난다 | [Lowest Common Ancestor of a Binary Search Tree](https://github.com/iamslash/learntocode/blob/master/leetcode/LowestCommonAncestorofaBinarySearchTree/MainApp.java) · [Lowest Common Ancestor of a Binary Tree](https://github.com/iamslash/learntocode/blob/master/leetcode/LowestCommonAncestorofaBinaryTree/MainApp.java) |

### Graphs

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Connected components | 정점과 간선, 또는 격자 | 몇 덩어리인가, 둘이 같은 덩어리인가, 어느 간선이 덩어리를 망치나 | 간선이 한꺼번에 주어지나 하나씩 들어오나 | [Number of Connected Components in an Undirected Graph](https://github.com/iamslash/learntocode/tree/master/leetcode/NumberofConnectedComponentsinanUndirectedGraph) · [Redundant Connection](https://github.com/iamslash/learntocode/tree/master/leetcode/RedundantConnection) |
| Topological order | 선행 관계가 있는 일들 | 실행 순서, 또는 그런 순서가 있기는 한가 | 사이클이 있으면 답이 없다. 그 판정이 문제의 절반 | [Course Schedule](https://github.com/iamslash/learntocode/blob/master/leetcode/CourseSchedule/MainApp.java) · [Course Schedule II](https://github.com/iamslash/learntocode/tree/master/leetcode/CourseScheduleII) |
| Shortest path | 그래프와 출발점, 필요하면 도착점 | 최소 비용 또는 최소 단계 | 가중치가 전부 1인가, 음수가 있나. 방법이 셋으로 갈린다 | [Word Ladder](https://github.com/iamslash/learntocode/blob/master/leetcode2/WordLadder/MainApp.java) · [Network Delay Time](https://github.com/iamslash/learntocode/blob/master/leetcode/NetworkDelayTime/MainApp.java) |
| Cycle | 그래프나 연결 리스트 | 사이클이 있나, 어디서 시작하나, 어디가 안 걸리나 | 다음이 하나뿐인가, 여러 갈래인가. 갈라지면 방문 중 상태를 따로 둬야 한다 | [Linked List Cycle II](https://github.com/iamslash/learntocode/tree/master/leetcode/LinkedListCycleII) · [Find Eventual Safe States](https://github.com/iamslash/learntocode/tree/master/leetcode/FindEventualSafeStates) |
| Spanning and flow | 가중치나 용량이 있는 그래프 | 전부 잇는 최소 비용, 최대로 흘릴 양, 최대 짝짓기 | 두 편으로 나뉘나. 나뉘면 매칭 문제가 된다 | [Min Cost to Connect All Points](https://github.com/iamslash/learntocode/blob/master/leetcode2/MinCosttoConnectAllPoints/MainApp.java) · [Maximum Number of Accepted Invitations](https://github.com/iamslash/learntocode/blob/master/leetcode2/MaximumNumberofAcceptedInvitations/MainApp.java) |

### States and Choices

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Carry state forward | 단계마다 고를 수 있는 상태가 몇 가지 | 마지막 단계의 최적값 | 상태 수를 미리 아나, 입력에 따라 늘어나나 | [Best Time to Buy and Sell Stock](https://github.com/iamslash/learntocode/blob/master/leetcode/BestTimetoBuyandSellStock/MainApp.java) · [Best Time to Buy and Sell Stock IV](https://github.com/iamslash/learntocode/tree/master/leetcode/BestTimetoBuyandSellStockIV) |
| Count the ways | 격자나 단계와 제약 | 끝까지 가는 방법의 수 | 갈 수 있는 곳이 처음부터 정해져 있나, 입력을 봐야 아나 | [Unique Paths](https://github.com/iamslash/learntocode/blob/master/leetcode/UniquePaths/MainApp.java) · [Decode Ways](https://github.com/iamslash/learntocode/blob/master/leetcode/DecodeWays/MainApp.java) |
| Interval DP | 한 줄과 구간 단위로 하는 연산 | 전체를 합치는 최적 비용 | 마지막에 무엇을 하느냐로 나뉘나 | [Burst Balloons](https://github.com/iamslash/learntocode/tree/master/leetcode/BurstBalloons) · [Strange Printer](https://github.com/iamslash/learntocode/tree/master/leetcode2/StrangePrinter) |
| Knapsack | 크기와 값이 있는 것들, 한도 | 한도나 목표를 두고 고른 최적값 | 같은 걸 여러 번 쓰나. 쓰면 순회 방향이 바뀐다 | [Ones and Zeroes](https://github.com/iamslash/learntocode/tree/master/leetcode/OnesandZeroes) · [Coin Change](https://github.com/iamslash/learntocode/blob/master/leetcode/CoinChange/MainApp.java) |
| List every arrangement | 작은 n 과 제약 | 조건을 만족하는 배치 전부 | 가지치기가 되나. 안 되면 답이 너무 많다 | [Letter Combinations of a Phone Number](https://github.com/iamslash/learntocode/blob/master/leetcode/LetterCombinationsofaPhoneNumber/MainApp.java) · [Generate Parentheses](https://github.com/iamslash/learntocode/blob/master/leetcode/GenerateParentheses/Solution.java) |
| Small n, every subset | n 이 20 안팎, 부분집합마다 값이 다름 | 전부 따져 얻은 최적값 | 부분집합만 상태로 쓰면 되나, 지금 어디인지도 같이 들고 가야 하나 | [Can I Win](https://github.com/iamslash/learntocode/tree/master/leetcode/CanIWin) · [Android Unlock Patterns](https://github.com/iamslash/learntocode/tree/master/leetcode/AndroidUnlockPatterns) |
| Win or lose | 번갈아 두는 게임 | 먼저 두는 쪽이 이기나 | 판이 독립된 더미로 쪼개지나. 쪼개지면 Grundy | [Nim Game](https://github.com/iamslash/learntocode/tree/master/leetcode/NimGame) · [Flip Game II](https://github.com/iamslash/learntocode/tree/master/leetcode/FlipGameII) |

### Numbers

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Digits and bases | 수 하나 또는 문자열로 적힌 수 | 자릿수를 다루거나 진법을 바꾼 결과 | 자료형 범위를 넘나. 넘으면 문자열로 센다 | [Reverse Integer](https://github.com/iamslash/learntocode/tree/master/leetcode/ReverseInteger) · [Excel Sheet Column Title](https://github.com/iamslash/learntocode/tree/master/leetcode/ExcelSheetColumnTitle) |
| Divisors and primes | 수 하나 또는 범위 | 소수인가, 소수가 몇 개인가, 약수가 무엇인가 | 하나를 보나 범위를 보나. 범위면 체를 만든다 | [Prime Palindrome](https://github.com/iamslash/learntocode/tree/master/leetcode/PrimePalindrome) · [Count Primes](https://github.com/iamslash/learntocode/tree/master/leetcode/CountPrimes) |
| Bit tricks | 수들 | 비트 연산으로 얻는 값 | 짝이 몇 개씩 맞나. 둘이면 XOR 한 번으로 끝난다 | [Single Number](https://github.com/iamslash/learntocode/blob/master/leetcode/SingleNumber/MainApp.java) · [Single Number II](https://github.com/iamslash/learntocode/tree/master/leetcode/SingleNumberII) |
| Combinatorics | n 과 법, 필요하면 k | 경우의 수 | 나눗셈이 들어가나. 들어가면 역원이 필요하다 | [Count All Valid Pickup and Delivery Options](https://github.com/iamslash/learntocode/tree/master/leetcode2/CountAllValidPickupandDeliveryOptions) · [Number of Ways to Reorder Array to Get Same BST](https://github.com/iamslash/learntocode/tree/master/leetcode2/NumberofWaystoReorderArraytoGetSameBST) |
| Chance and sampling | 무작위가 필요한 상황 | 균등하게 뽑은 결과 | 전체 크기를 미리 아나. 모르면 흘러가며 뽑는다 | [Shuffle an Array](https://github.com/iamslash/learntocode/tree/master/leetcode/ShuffleanArray) · [Linked List Random Node](https://github.com/iamslash/learntocode/tree/master/leetcode/LinkedListRandomNode) |
| Geometry | 점이나 도형 | 거리, 포함 관계, 또는 감싸는 모양 | 실수를 쓰나. 쓰면 오차가 문제의 절반이다 | [Max Points on a Line](https://github.com/iamslash/learntocode/tree/master/leetcode/MaxPointsonaLine) · [Generate Random Point in a Circle](https://github.com/iamslash/learntocode/tree/master/leetcode/GenerateRandomPointinaCircle) |

### Data Structures

| 문제 | In | Out | 가르는 조건 | 예 |
|---|---|---|---|---|
| Design a structure | 연산 목록과 시간 제약 | 그 연산들이 전부 빠른 자료구조 | 넣을 때 일을 해두나, 꺼낼 때 하나 | [Two Sum III - Data structure design](https://github.com/iamslash/learntocode/tree/master/leetcode/TwoSumIII-Datastructuredesign) · [Design Twitter](https://github.com/iamslash/learntocode/blob/master/leetcode/DesignTwitter/Solution.java) |
| Cache and eviction | 용량 제한과 접근 기록 | 무엇을 남기고 무엇을 버릴지 정하는 구조 | 버리는 기준이 시간인가 횟수인가 | [LRU Cache](https://github.com/iamslash/learntocode/blob/master/leetcode/LRUCache/MainApp.java) · [LFU Cache](https://github.com/iamslash/learntocode/blob/master/leetcode2/LFUCache/MainApp.java) |
| Stack and queue discipline | 한쪽 끝에서만 넣고 빼는 규칙 | 그 규칙을 지키면서 추가 질의에 답하는 구조 | 최솟값 같은 걸 같이 물어보나 | [Min Stack](https://github.com/iamslash/learntocode/blob/master/leetcode/MinStack/Solution.java) · [Implement Stack using Queues](https://github.com/iamslash/learntocode/blob/master/leetcode/ImplementStackusingQueues/MainApp.java) |
| Key to value | 키와 값, 그리고 요구되는 연산 | 넣고 빼고 찾기가 전부 상수 시간인 구조 | 무작위 추출이 끼어 있나. 있으면 배열을 같이 둔다 | [Design HashMap](https://github.com/iamslash/learntocode/blob/master/leetcode/DesignHashMap/MyHashMap.20200714.java) · [Insert Delete GetRandom O(1) - Duplicates allowed](https://github.com/iamslash/learntocode/tree/master/leetcode2/InsertDeleteGetRandomO%281%29-Duplicatesallowed) |
| Iterate on demand | 중첩되거나 압축된 데이터 | 하나씩 꺼내 주는 반복자 | 미리 다 펼쳐도 되나. 안 되면 게으르게 만든다 | [Flatten Nested List Iterator](https://github.com/iamslash/learntocode/tree/master/leetcode/FlattenNestedListIterator) · [Binary Search Tree Iterator](https://github.com/iamslash/learntocode/blob/master/leetcode/BinarySearchTreeIterator/MainApp.java) |
| Linked list surgery | 노드로 이어진 줄 | 뒤집기, 자르기, 합치기, 사이클 찾기 | 길이를 미리 아나. 모르면 포인터 둘을 쓴다 | [Remove Nth Node From End of List](https://github.com/iamslash/learntocode/tree/master/leetcode/RemoveNthNodeFromEndofList) · [Reverse Linked List II](https://github.com/iamslash/learntocode/tree/master/leetcode/ReverseLinkedListII) |

## 3. 쓰는 법

왼쪽 세 칸을 보고 오른쪽을 가립니다. 지문을 읽었을 때 **가르는 조건에
답할 수 있으면** 그 문제는 풀립니다. 답이 안 나오면 거기가 다시 볼 자리입니다.

