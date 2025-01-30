---
title: "[leetcode] Minimum Cost for Cutting Cake I"
slug: "[leetcode] Minimum Cost for Cutting Cake I"
tags:
  - leetcode
---


[\[leetcode] Minimum Cost for Cutting Cake I](https://leetcode.com/problems/minimum-cost-for-cutting-cake-i/description/)

[\[learntocode] Minimum Cost for Cutting Cake I](https://github.com/iamslash/learntocode/blob/master/leetcode4/MinimumCostforCuttingCakeI/MainApp.java)\
\
This problem involves calculating the minimum cost required to cut a large cake into 1x1 pieces. There are two ways to cut the cake: horizontally and vertically, each with a specific cost. Our goal is to find the optimal way to minimize the total cutting cost.

## Approach to Solving the Problem

### 1. Cut the Most Expensive Line First

The reason for cutting the most expensive line first is that doing so results in more pieces being divided, which improves cost efficiency.\
For example, if the cost of a vertical cut is 5 and the cost of a horizontal cut is 3, it is usually more economical to make the vertical cut first and then proceed with the horizontal cuts.

### 2. Sort the Costs

Sort the costs for horizontal and vertical cuts in descending order. This allows us to process the most expensive cuts first.

### 3. Determine the Cutting Order

Using the sorted cost lists, compare each cost one by one.\
Always cut the more expensive line first, multiplying the cost by the current number of cake pieces in the corresponding direction.\
For example, if the cake is initially one whole piece, the cost is added directly. However, as the cake is cut into more pieces, costs accumulate accordingly.

### 4. Increase the Number of Pieces

* A horizontal cut increases the number of vertical pieces (`vPieces`).
* A vertical cut increases the number of horizontal pieces (`hPieces`).\
  We continue managing the number of pieces this way until all cuts are made.

## Understanding Through an Example

### Example 1

**Input:**\
m = 3, n = 2, horizontalCut = \[1,3], verticalCut = \[5]

**Step-by-step breakdown:**

* **Horizontal costs:** \[1, 3] → No sorting needed.
* **Vertical costs:** \[5]

Since the vertical cost (5) is greater than any horizontal cost, we make the vertical cut first.

* **Cost:** 5 × 1 (number of horizontal pieces) → 5
* **Increase vertical pieces:** `vPieces = 2`

Next, among the remaining horizontal costs \[1, 3], we cut the larger cost (3) first.

* **Cost:** 3 × 2 (number of vertical pieces) → 6
* **Increase horizontal pieces:** `hPieces = 2`

Finally, we make the last horizontal cut (cost 1).

* **Cost:** 1 × 2 (number of vertical pieces) → 2
* **Increase horizontal pieces:** `hPieces = 3`

**Final total cost:** 5 + 6 + 2 = 13

## Time and Space Complexity

### Time Complexity:

* Sorting the horizontal and vertical costs takes **O(H log H)** and **O(V log V)**, respectively.
* After sorting, comparing costs and iterating through the lists takes **O(H + V)**.
* Therefore, the overall time complexity is **O(H log H + V log V)**.

### Space Complexity:

* Additional memory is only used during sorting, so the space complexity is **O(1)**.