from __future__ import annotations

import math
from collections import Counter, deque
from dataclasses import dataclass

from .model import Difficulty


@dataclass(frozen=True)
class CatalogCase:
    input_data: str
    output_data: str
    is_hidden: bool


@dataclass(frozen=True)
class CatalogQuestion:
    title: str
    description: str
    difficulty: Difficulty
    cases: tuple[CatalogCase, ...]


@dataclass(frozen=True)
class CatalogContest:
    title: str
    description: str
    duration: int
    questions: tuple[CatalogQuestion, ...]


OPERATION_DOCS = {
    "sum": "Read n followed by n integers. Print their sum.",
    "two_sum_indices": "Read n and target followed by n integers. Print the first pair of zero-based indices whose values sum to target.",
    "reverse_words": "Read one line and print its words in reverse order with single spaces.",
    "palindrome": "Read one line. Ignore non-alphanumeric characters and case, then print true if it is a palindrome.",
    "reverse": "Read n followed by n integers. Print the values in reverse order.",
    "distinct": "Read n followed by n integers. Print the number of distinct values.",
    "prefix": "Read n followed by n integers. Print the inclusive prefix sums.",
    "max_subarray": "Read n followed by n integers. Print the maximum non-empty contiguous subarray sum.",
    "product_except": "Read n followed by n integers. Print the product of all values except the current index, without division.",
    "longest_unique": "Read one line. Print the length of its longest substring without repeated characters.",
    "target_count": "Read n and target, then n integers. Print how many times target occurs.",
    "sorted": "Read n followed by n integers. Print true if they are in non-decreasing order, otherwise false.",
    "rotate": "Read n and k, then n integers. Rotate the array right by k and print it.",
    "binary_search": "Read n and target, then a sorted array. Print the zero-based target index or -1.",
    "gcd": "Read two integers and print their greatest common divisor.",
    "kth_smallest": "Read n and k followed by n integers. Print the kth smallest value, where k is one-based.",
    "lis": "Read n followed by n integers. Print the length of the longest strictly increasing subsequence.",
    "coin_change": "Read amount and coin count, then the coin values. Print the minimum coins needed, or -1.",
    "subset_sum": "Read n and target followed by n non-negative integers. Print true if a subset sums to target.",
    "intervals": "Read n intervals. Print the maximum number of non-overlapping intervals selectable.",
    "fibonacci": "Read n and print the nth Fibonacci number with F(0)=0 and F(1)=1.",
    "edit_distance": "Read two lines and print their Levenshtein edit distance.",
    "grid_paths": "Read rows and columns. Print the number of paths from top-left to bottom-right using only down and right.",
    "merge_sorted": "Read n and m followed by two sorted arrays. Print their sorted merge.",
    "balanced": "Read a bracket string containing (), {}, and []. Print true when it is balanced.",
    "next_greater": "Read n followed by n integers. Print the next greater value to the right for each item, or -1.",
    "pair_sum": "Read n and target followed by n integers. Print true if two different values sum to target.",
    "anagram": "Read two lines. Print true if the lowercase strings are anagrams.",
    "majority": "Read n followed by n integers. Print the value appearing more than n/2 times, or -1.",
    "first_unique": "Read one line. Print the first non-repeating character, or -1.",
    "intersection": "Read n and m, then two integer arrays. Print the sorted distinct intersection.",
    "longest_consecutive": "Read n followed by n integers. Print the length of the longest consecutive-value sequence.",
    "subarray_count": "Read n and target followed by n integers. Print the number of contiguous subarrays summing to target.",
    "top_frequency": "Read n and k followed by n integers. Print the k most frequent values, breaking ties by smaller value.",
    "window_max_sum": "Read n and k followed by n integers. Print the largest sum of any length-k window.",
    "window_min_len": "Read n and target followed by positive integers. Print the minimum window length with sum at least target, or 0.",
    "window_distinct": "Read n and k followed by n integers. Print the distinct-value count for every length-k window.",
    "max_ones": "Read n and k followed by a binary array. Print the longest run of ones after flipping at most k zeros.",
    "anagram_windows": "Read text and pattern on separate lines. Print the number of pattern-anagram windows in text.",
    "postfix": "Read a space-separated postfix expression with integer operands. Print its value.",
    "min_removals": "Read a parentheses string. Print the minimum removals needed to make it valid.",
    "histogram": "Read n followed by bar heights. Print the largest rectangle area.",
    "simplify_path": "Read an absolute Unix path and print its canonical simplified path.",
    "decode_repeat": "Read an encoded string such as 3[a2[c]]. Print the decoded string.",
    "permutation_count": "Read n distinct integers. Print the number of permutations.",
    "combination_count": "Read n and target followed by positive distinct integers. Print the number of combinations that sum to target.",
    "jump_game": "Read n followed by maximum jump lengths. Print true if the last index is reachable.",
    "gas_station": "Read n, then gas amounts and costs. Print a valid starting station index, or -1.",
    "assign_cookies": "Read child and cookie counts, then greed factors and cookie sizes. Print the maximum satisfied children.",
    "knapsack": "Read n and capacity, then weights and values. Print the maximum 0/1 knapsack value.",
    "tree_height": "Read n and then the parent of nodes 1 through n-1 in a rooted tree at 0. Print tree height in nodes.",
    "tree_leaves": "Read n and then the parent of nodes 1 through n-1. Print the number of leaf nodes.",
    "graph_shortest": "Read n, m, source, target followed by undirected edges. Print the unweighted shortest distance, or -1.",
    "components": "Read n and m followed by undirected edges. Print the number of connected components.",
    "topological": "Read n and m followed by directed edges. Print true if the graph is acyclic, otherwise false.",
    "bipartite": "Read n and m followed by undirected edges. Print true if the graph is bipartite.",
    "islands": "Read rows and columns followed by a 0/1 grid. Print the number of four-directional islands.",
    "degree_max": "Read n and m followed by undirected edges. Print the highest vertex degree.",
}


CASES: dict[str, tuple[str, ...]] = {
    "sum": ("5\n1 2 3 4 5\n", "3\n-4 7 2\n", "1\n9\n", "4\n0 0 0 0\n", "6\n10 -2 8 -6 4 1\n"),
    "two_sum_indices": ("4 9\n2 7 11 15\n", "3 6\n3 2 4\n", "5 10\n1 8 5 2 9\n", "4 0\n-3 4 3 90\n", "6 12\n5 1 7 4 8 3\n"),
    "reverse_words": ("the sky is blue\n", "hello world\n", "  code   every day  \n", "single\n", "a good   example\n"),
    "palindrome": ("A man, a plan, a canal: Panama\n", "race a car\n", "No 'x' in Nixon\n", "0P\n", "Was it a car or a cat I saw?\n"),
    "reverse": ("4\n1 2 3 4\n", "3\n-1 0 8\n", "1\n7\n", "5\n2 2 3 2 1\n", "6\n9 8 7 6 5 4\n"),
    "distinct": ("5\n1 2 2 3 1\n", "4\n7 7 7 7\n", "1\n-2\n", "6\n-1 0 -1 2 0 3\n", "8\n1 2 3 4 5 6 7 8\n"),
    "prefix": ("4\n1 2 3 4\n", "3\n-2 5 -1\n", "1\n9\n", "5\n0 1 0 1 0\n", "6\n10 -10 3 4 -2 5\n"),
    "max_subarray": ("9\n-2 1 -3 4 -1 2 1 -5 4\n", "4\n-8 -3 -6 -2\n", "1\n5\n", "6\n1 2 3 -10 4 5\n", "5\n0 0 0 0 0\n"),
    "product_except": ("4\n1 2 3 4\n", "5\n-1 1 0 -3 3\n", "3\n2 3 4\n", "4\n0 0 2 3\n", "2\n-5 6\n"),
    "longest_unique": ("abcabcbb\n", "bbbbb\n", "pwwkew\n", "dvdf\n", "abba\n"),
    "target_count": ("6 2\n1 2 2 3 2 4\n", "4 9\n9 9 9 9\n", "3 0\n1 2 3\n", "5 -1\n-1 0 -1 2 -1\n", "1 7\n7\n"),
    "sorted": ("5\n1 2 2 3 9\n", "4\n4 3 2 1\n", "1\n8\n", "5\n-2 -2 0 4 3\n", "6\n-5 -1 0 0 7 10\n"),
    "rotate": ("5 2\n1 2 3 4 5\n", "4 0\n9 8 7 6\n", "3 5\n1 2 3\n", "1 99\n7\n", "6 3\n-1 0 1 2 3 4\n"),
    "binary_search": ("6 9\n-1 0 3 5 9 12\n", "6 2\n-1 0 3 5 9 12\n", "1 7\n7\n", "7 -5\n-9 -5 -1 0 4 8 12\n", "5 10\n1 3 5 7 9\n"),
    "gcd": ("48 18\n", "7 13\n", "0 9\n", "-24 36\n", "270 192\n"),
    "kth_smallest": ("5 2\n5 1 4 2 3\n", "4 4\n7 7 2 9\n", "1 1\n-3\n", "6 3\n10 -1 4 4 8 2\n", "7 5\n9 0 3 6 2 8 1\n"),
    "lis": ("8\n10 9 2 5 3 7 101 18\n", "6\n0 1 0 3 2 3\n", "1\n5\n", "5\n5 4 3 2 1\n", "7\n1 3 2 4 3 5 4\n"),
    "coin_change": ("11 3\n1 2 5\n", "3 1\n2\n", "0 2\n2 3\n", "27 4\n1 5 10 25\n", "7 2\n2 4\n"),
    "subset_sum": ("5 9\n3 34 4 12 5\n", "4 30\n3 4 5 6\n", "3 0\n1 2 3\n", "6 17\n2 4 6 9 11 13\n", "1 8\n8\n"),
    "intervals": ("4\n1 3\n2 4\n3 5\n6 8\n", "3\n1 10\n2 3\n4 5\n", "1\n0 1\n", "5\n1 2\n2 3\n3 4\n4 5\n5 6\n", "4\n0 5\n1 2\n2 3\n3 4\n"),
    "fibonacci": ("0\n", "1\n", "7\n", "10\n", "20\n"),
    "edit_distance": ("kitten\nsitting\n", "flaw\nlawn\n", "a\na\n", "\nabc\n", "algorithm\naltruistic\n"),
    "grid_paths": ("3 3\n", "1 5\n", "2 2\n", "4 3\n", "6 6\n"),
    "merge_sorted": ("3 3\n1 3 5\n2 4 6\n", "0 3\n\n1 2 3\n", "4 2\n-5 -1 0 8\n-3 7\n", "3 4\n1 1 2\n1 2 2 3\n", "2 2\n10 20\n-1 30\n"),
    "balanced": ("()[]{}\n", "(]\n", "{[()]}\n", "([)]\n", "(((())))\n"),
    "next_greater": ("4\n2 1 2 4\n", "5\n5 4 3 2 1\n", "1\n7\n", "6\n1 3 2 5 4 6\n", "4\n-2 -1 -3 0\n"),
    "pair_sum": ("4 9\n2 7 11 15\n", "3 6\n3 2 4\n", "4 20\n1 2 3 4\n", "5 0\n-3 1 3 8 2\n", "2 10\n5 5\n"),
    "anagram": ("listen\nsilent\n", "rat\ncar\n", "a\na\n", "triangle\nintegral\n", "hello\nbello\n"),
    "majority": ("7\n2 2 1 1 1 2 2\n", "4\n1 2 3 4\n", "1\n9\n", "5\n-1 -1 -1 2 3\n", "6\n3 3 4 2 3 3\n"),
    "first_unique": ("leetcode\n", "aabb\n", "z\n", "swiss\n", "alphabet\n"),
    "intersection": ("4 5\n1 2 2 4\n2 2 3 4 5\n", "3 2\n1 3 5\n2 4\n", "1 1\n7\n7\n", "5 4\n-1 0 2 3 3\n3 -1 8 9\n", "3 5\n1 2 3\n1 2 3 4 5\n"),
    "longest_consecutive": ("6\n100 4 200 1 3 2\n", "9\n0 3 7 2 5 8 4 6 1\n", "1\n5\n", "5\n1 2 0 1 3\n", "6\n-2 -1 0 2 3 4\n"),
    "subarray_count": ("3 2\n1 1 1\n", "3 3\n1 2 3\n", "5 0\n1 -1 0 2 -2\n", "1 5\n5\n", "6 4\n2 2 2 2 -2 2\n"),
    "top_frequency": ("6 2\n1 1 1 2 2 3\n", "5 1\n4 4 5 5 5\n", "4 3\n3 1 2 3\n", "7 2\n-1 -1 2 2 3 3 3\n", "8 4\n1 2 3 4 1 2 3 4\n"),
    "window_max_sum": ("6 3\n2 1 5 1 3 2\n", "4 2\n-5 -2 -3 -4\n", "1 1\n7\n", "5 5\n1 2 3 4 5\n", "7 4\n4 0 -1 3 5 -2 6\n"),
    "window_min_len": ("6 7\n2 3 1 2 4 3\n", "5 15\n1 2 3 4 5\n", "4 100\n1 2 3 4\n", "1 5\n5\n", "6 8\n8 1 1 1 1 1\n"),
    "window_distinct": ("7 4\n1 2 1 3 4 2 3\n", "4 2\n1 1 1 1\n", "1 1\n5\n", "5 3\n-1 0 -1 2 0\n", "6 6\n1 2 3 4 5 6\n"),
    "max_ones": ("11 2\n1 1 1 0 0 0 1 1 1 1 0\n", "5 0\n1 0 1 1 0\n", "4 4\n0 0 0 0\n", "1 0\n1\n", "8 1\n0 1 1 0 1 1 1 0\n"),
    "anagram_windows": ("cbaebabacd\nabc\n", "abab\nab\n", "aaaa\naa\n", "abc\nd\n", "listeningsilent\nlisten\n"),
    "postfix": ("2 3 +\n", "5 1 2 + 4 * + 3 -\n", "8 2 /\n", "7 2 3 * -\n", "4 2 + 3 5 1 - * +\n"),
    "min_removals": ("lee(t(c)o)de)\n", "a)b(c)d\n", ")(\n", "((abc))\n", "(()))(()\n"),
    "histogram": ("6\n2 1 5 6 2 3\n", "2\n2 4\n", "1\n7\n", "5\n1 2 3 4 5\n", "4\n4 4 4 4\n"),
    "simplify_path": ("/home/\n", "/../\n", "/home//foo/\n", "/a/./b/../../c/\n", "/a//b////c/d//././/..\n"),
    "decode_repeat": ("3[a]2[bc]\n", "3[a2[c]]\n", "2[abc]3[cd]ef\n", "10[x]\n", "a2[b3[c]]d\n"),
    "permutation_count": ("1\n7\n", "3\n1 2 3\n", "5\n1 2 3 4 5\n", "0\n\n", "8\n1 2 3 4 5 6 7 8\n"),
    "combination_count": ("4 7\n2 3 6 7\n", "3 8\n2 3 5\n", "2 1\n2 4\n", "1 9\n3\n", "5 10\n1 2 5 6 7\n"),
    "jump_game": ("5\n2 3 1 1 4\n", "5\n3 2 1 0 4\n", "1\n0\n", "6\n2 0 2 0 1 0\n", "4\n1 1 0 1\n"),
    "gas_station": ("5\n1 2 3 4 5\n3 4 5 1 2\n", "3\n2 3 4\n3 4 3\n", "1\n5\n4\n", "4\n4 1 2 3\n2 2 2 2\n", "4\n1 1 1 10\n2 2 2 2\n"),
    "assign_cookies": ("3 2\n1 2 3\n1 1\n", "2 3\n1 2\n1 2 3\n", "1 1\n5\n4\n", "4 4\n2 3 1 4\n1 1 3 5\n", "3 5\n1 1 1\n1 1 1 1 1\n"),
    "knapsack": ("3 50\n10 20 30\n60 100 120\n", "4 7\n1 3 4 5\n1 4 5 7\n", "1 4\n5\n10\n", "5 10\n2 2 6 5 4\n6 3 5 4 6\n", "3 0\n1 2 3\n4 5 6\n"),
    "tree_height": ("5\n0 0 1 1\n", "1\n\n", "6\n0 1 2 3 4\n", "7\n0 0 0 0 0 0\n", "8\n0 0 1 1 3 3 6\n"),
    "tree_leaves": ("5\n0 0 1 1\n", "1\n\n", "6\n0 1 2 3 4\n", "7\n0 0 0 0 0 0\n", "8\n0 0 1 1 3 3 6\n"),
    "graph_shortest": ("5 5 0 4\n0 1\n1 2\n2 4\n0 3\n3 4\n", "4 2 0 3\n0 1\n2 3\n", "1 0 0 0\n", "6 5 1 5\n1 2\n2 3\n3 4\n4 5\n0 5\n", "5 4 2 0\n0 1\n1 2\n2 3\n3 4\n"),
    "components": ("5 3\n0 1\n1 2\n3 4\n", "4 0\n", "1 0\n", "6 5\n0 1\n1 2\n2 3\n3 4\n4 5\n", "7 3\n0 1\n2 3\n4 5\n"),
    "topological": ("4 3\n0 1\n1 2\n2 3\n", "3 3\n0 1\n1 2\n2 0\n", "1 0\n", "5 5\n0 1\n0 2\n1 3\n2 3\n3 4\n", "4 4\n0 1\n1 2\n2 3\n3 1\n"),
    "bipartite": ("4 4\n0 1\n1 2\n2 3\n3 0\n", "3 3\n0 1\n1 2\n2 0\n", "1 0\n", "5 3\n0 1\n2 3\n3 4\n", "6 6\n0 1\n1 2\n2 3\n3 4\n4 5\n5 0\n"),
    "islands": ("3 4\n1100\n0101\n0011\n", "2 2\n00\n00\n", "1 1\n1\n", "4 5\n11000\n11000\n00100\n00011\n", "3 3\n101\n010\n101\n"),
    "degree_max": ("5 4\n0 1\n0 2\n0 3\n3 4\n", "4 0\n", "2 1\n0 1\n", "6 5\n0 1\n1 2\n2 3\n3 4\n4 5\n", "4 6\n0 1\n0 2\n0 3\n1 2\n1 3\n2 3\n"),
}


def _array(tokens: list[str]) -> list[int]:
    n = int(tokens[0])
    return [int(value) for value in tokens[1:1 + n]]


def solve_reference(operation: str, input_data: str) -> str:
    tokens = input_data.split()
    if operation == "two_sum_indices":
        n, target = map(int, tokens[:2])
        values = list(map(int, tokens[2:2 + n]))
        seen: dict[int, int] = {}
        result = ""
        for index, value in enumerate(values):
            complement = target - value
            if complement in seen:
                result = f"{seen[complement]} {index}"
                break
            seen.setdefault(value, index)
    elif operation == "reverse_words":
        result = " ".join(reversed(input_data.split()))
    elif operation == "palindrome":
        normalized = "".join(char.lower() for char in input_data if char.isalnum())
        result = str(normalized == normalized[::-1]).lower()
    elif operation in {"sum", "reverse", "distinct", "prefix", "max_subarray", "product_except", "sorted"}:
        values = _array(tokens)
        if operation == "sum":
            result = str(sum(values))
        elif operation == "reverse":
            result = " ".join(map(str, reversed(values)))
        elif operation == "distinct":
            result = str(len(set(values)))
        elif operation == "prefix":
            running = 0
            prefixes = []
            for value in values:
                running += value
                prefixes.append(running)
            result = " ".join(map(str, prefixes))
        elif operation == "max_subarray":
            current = best = values[0]
            for value in values[1:]:
                current = max(value, current + value)
                best = max(best, current)
            result = str(best)
        elif operation == "product_except":
            output = []
            for index in range(len(values)):
                output.append(math.prod(values[:index] + values[index + 1:]))
            result = " ".join(map(str, output))
        else:
            result = str(all(a <= b for a, b in zip(values, values[1:]))).lower()
    elif operation == "longest_unique":
        text = input_data.rstrip("\n")
        left = best = 0
        seen: dict[str, int] = {}
        for right, char in enumerate(text):
            left = max(left, seen.get(char, -1) + 1)
            seen[char] = right
            best = max(best, right - left + 1)
        result = str(best)
    elif operation in {"target_count", "binary_search", "pair_sum", "subarray_count"}:
        n, target = map(int, tokens[:2])
        values = list(map(int, tokens[2:2 + n]))
        if operation == "target_count":
            result = str(values.count(target))
        elif operation == "binary_search":
            lo, hi, found = 0, n - 1, -1
            while lo <= hi:
                mid = (lo + hi) // 2
                if values[mid] == target:
                    found = mid
                    break
                if values[mid] < target:
                    lo = mid + 1
                else:
                    hi = mid - 1
            result = str(found)
        elif operation == "pair_sum":
            seen = set()
            found = False
            for value in values:
                if target - value in seen:
                    found = True
                    break
                seen.add(value)
            result = str(found).lower()
        else:
            counts = Counter({0: 1})
            prefix = answer = 0
            for value in values:
                prefix += value
                answer += counts[prefix - target]
                counts[prefix] += 1
            result = str(answer)
    elif operation == "rotate":
        n, k = map(int, tokens[:2])
        values = list(map(int, tokens[2:2 + n]))
        k %= n
        result = " ".join(map(str, values[-k:] + values[:-k] if k else values))
    elif operation == "gcd":
        result = str(math.gcd(int(tokens[0]), int(tokens[1])))
    elif operation == "kth_smallest":
        n, k = map(int, tokens[:2])
        result = str(sorted(map(int, tokens[2:2 + n]))[k - 1])
    elif operation == "lis":
        values = _array(tokens)
        tails: list[int] = []
        for value in values:
            lo, hi = 0, len(tails)
            while lo < hi:
                mid = (lo + hi) // 2
                if tails[mid] < value:
                    lo = mid + 1
                else:
                    hi = mid
            if lo == len(tails):
                tails.append(value)
            else:
                tails[lo] = value
        result = str(len(tails))
    elif operation == "coin_change":
        amount, count = map(int, tokens[:2])
        coins = list(map(int, tokens[2:2 + count]))
        dp = [amount + 1] * (amount + 1)
        dp[0] = 0
        for value in range(1, amount + 1):
            for coin in coins:
                if coin <= value:
                    dp[value] = min(dp[value], dp[value - coin] + 1)
        result = str(dp[amount] if dp[amount] <= amount else -1)
    elif operation == "subset_sum":
        n, target = map(int, tokens[:2])
        possible = {0}
        for value in map(int, tokens[2:2 + n]):
            possible |= {subtotal + value for subtotal in tuple(possible)}
        result = str(target in possible).lower()
    elif operation == "intervals":
        n = int(tokens[0])
        pairs = [(int(tokens[i]), int(tokens[i + 1])) for i in range(1, 2 * n + 1, 2)]
        end = -10**18
        selected = 0
        for start, finish in sorted(pairs, key=lambda pair: (pair[1], pair[0])):
            if start >= end:
                selected += 1
                end = finish
        result = str(selected)
    elif operation == "fibonacci":
        n = int(tokens[0])
        a, b = 0, 1
        for _ in range(n):
            a, b = b, a + b
        result = str(a)
    elif operation == "edit_distance":
        first, second = input_data.splitlines()[:2]
        previous = list(range(len(second) + 1))
        for i, left in enumerate(first, 1):
            current = [i]
            for j, right in enumerate(second, 1):
                current.append(min(current[-1] + 1, previous[j] + 1, previous[j - 1] + (left != right)))
            previous = current
        result = str(previous[-1])
    elif operation == "grid_paths":
        rows, columns = map(int, tokens[:2])
        result = str(math.comb(rows + columns - 2, rows - 1))
    elif operation == "merge_sorted":
        n, m = map(int, tokens[:2])
        values = sorted(map(int, tokens[2:2 + n + m]))
        result = " ".join(map(str, values))
    elif operation == "balanced":
        pairs = {")": "(", "]": "[", "}": "{"}
        stack = []
        valid = True
        for char in input_data.strip():
            if char in "([{":
                stack.append(char)
            elif not stack or stack.pop() != pairs[char]:
                valid = False
                break
        result = str(valid and not stack).lower()
    elif operation == "next_greater":
        values = _array(tokens)
        output = [-1] * len(values)
        stack: list[int] = []
        for index, value in enumerate(values):
            while stack and values[stack[-1]] < value:
                output[stack.pop()] = value
            stack.append(index)
        result = " ".join(map(str, output))
    elif operation == "anagram":
        first, second = input_data.splitlines()[:2]
        result = str(Counter(first) == Counter(second)).lower()
    elif operation == "majority":
        values = _array(tokens)
        counts = Counter(values)
        value, frequency = counts.most_common(1)[0]
        result = str(value if frequency > len(values) // 2 else -1)
    elif operation == "first_unique":
        text = input_data.strip()
        counts = Counter(text)
        result = next((char for char in text if counts[char] == 1), "-1")
    elif operation == "intersection":
        n, m = map(int, tokens[:2])
        first = set(map(int, tokens[2:2 + n]))
        second = set(map(int, tokens[2 + n:2 + n + m]))
        result = " ".join(map(str, sorted(first & second)))
    elif operation == "longest_consecutive":
        values = set(_array(tokens))
        best = 0
        for value in values:
            if value - 1 not in values:
                length = 1
                while value + length in values:
                    length += 1
                best = max(best, length)
        result = str(best)
    elif operation == "top_frequency":
        n, k = map(int, tokens[:2])
        counts = Counter(map(int, tokens[2:2 + n]))
        result = " ".join(str(value) for value, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:k])
    elif operation in {"window_max_sum", "window_min_len", "window_distinct", "max_ones"}:
        n, k = map(int, tokens[:2])
        values = list(map(int, tokens[2:2 + n]))
        if operation == "window_max_sum":
            current = sum(values[:k])
            best = current
            for index in range(k, n):
                current += values[index] - values[index - k]
                best = max(best, current)
            result = str(best)
        elif operation == "window_min_len":
            target = k
            left = total = 0
            best = n + 1
            for right, value in enumerate(values):
                total += value
                while total >= target:
                    best = min(best, right - left + 1)
                    total -= values[left]
                    left += 1
            result = str(0 if best == n + 1 else best)
        elif operation == "window_distinct":
            result = " ".join(str(len(set(values[index:index + k]))) for index in range(n - k + 1))
        else:
            left = zeros = best = 0
            for right, value in enumerate(values):
                zeros += value == 0
                while zeros > k:
                    zeros -= values[left] == 0
                    left += 1
                best = max(best, right - left + 1)
            result = str(best)
    elif operation == "anagram_windows":
        text, pattern = input_data.splitlines()[:2]
        target = Counter(pattern)
        size = len(pattern)
        result = str(sum(Counter(text[index:index + size]) == target for index in range(len(text) - size + 1)))
    elif operation == "postfix":
        stack: list[int] = []
        for token in tokens:
            if token.lstrip("-").isdigit():
                stack.append(int(token))
            else:
                right, left = stack.pop(), stack.pop()
                stack.append({"+": left + right, "-": left - right, "*": left * right, "/": int(left / right)}[token])
        result = str(stack[-1])
    elif operation == "min_removals":
        balance = removals = 0
        for char in input_data.strip():
            if char == "(":
                balance += 1
            elif char == ")":
                if balance:
                    balance -= 1
                else:
                    removals += 1
        result = str(removals + balance)
    elif operation == "histogram":
        heights = _array(tokens) + [0]
        stack: list[int] = []
        best = 0
        for index, height in enumerate(heights):
            while stack and heights[stack[-1]] > height:
                popped = stack.pop()
                width = index if not stack else index - stack[-1] - 1
                best = max(best, heights[popped] * width)
            stack.append(index)
        result = str(best)
    elif operation == "simplify_path":
        stack = []
        for part in input_data.strip().split("/"):
            if part in {"", "."}:
                continue
            if part == "..":
                if stack:
                    stack.pop()
            else:
                stack.append(part)
        result = "/" + "/".join(stack)
    elif operation == "decode_repeat":
        stack: list[tuple[str, int]] = []
        current = ""
        number = 0
        for char in input_data.strip():
            if char.isdigit():
                number = number * 10 + int(char)
            elif char == "[":
                stack.append((current, number))
                current, number = "", 0
            elif char == "]":
                prefix, repeat = stack.pop()
                current = prefix + current * repeat
            else:
                current += char
        result = current
    elif operation == "permutation_count":
        result = str(math.factorial(int(tokens[0])))
    elif operation == "combination_count":
        n, target = map(int, tokens[:2])
        values = list(map(int, tokens[2:2 + n]))
        dp = [0] * (target + 1)
        dp[0] = 1
        for value in values:
            for subtotal in range(value, target + 1):
                dp[subtotal] += dp[subtotal - value]
        result = str(dp[target])
    elif operation == "jump_game":
        values = _array(tokens)
        farthest = 0
        for index, jump in enumerate(values):
            if index > farthest:
                break
            farthest = max(farthest, index + jump)
        result = str(farthest >= len(values) - 1).lower()
    elif operation == "gas_station":
        n = int(tokens[0])
        gas = list(map(int, tokens[1:1 + n]))
        costs = list(map(int, tokens[1 + n:1 + 2 * n]))
        if sum(gas) < sum(costs):
            result = "-1"
        else:
            start = tank = 0
            for index, (gain, cost) in enumerate(zip(gas, costs)):
                tank += gain - cost
                if tank < 0:
                    start, tank = index + 1, 0
            result = str(start)
    elif operation == "assign_cookies":
        children, cookies = map(int, tokens[:2])
        greed = sorted(map(int, tokens[2:2 + children]))
        sizes = sorted(map(int, tokens[2 + children:2 + children + cookies]))
        child = 0
        for size in sizes:
            if child < children and size >= greed[child]:
                child += 1
        result = str(child)
    elif operation == "knapsack":
        n, capacity = map(int, tokens[:2])
        weights = list(map(int, tokens[2:2 + n]))
        values = list(map(int, tokens[2 + n:2 + 2 * n]))
        dp = [0] * (capacity + 1)
        for weight, value in zip(weights, values):
            for current in range(capacity, weight - 1, -1):
                dp[current] = max(dp[current], dp[current - weight] + value)
        result = str(dp[capacity])
    elif operation in {"tree_height", "tree_leaves"}:
        n = int(tokens[0])
        parents = list(map(int, tokens[1:]))
        children = [[] for _ in range(n)]
        for node, parent in enumerate(parents, 1):
            children[parent].append(node)
        if operation == "tree_leaves":
            result = str(sum(not nodes for nodes in children))
        else:
            queue = deque([(0, 1)])
            best = 0
            while queue:
                node, depth = queue.popleft()
                best = max(best, depth)
                queue.extend((child, depth + 1) for child in children[node])
            result = str(best)
    elif operation in {"graph_shortest", "components", "topological", "bipartite", "degree_max"}:
        if operation == "graph_shortest":
            n, m, source, target = map(int, tokens[:4])
            edge_tokens = tokens[4:]
        else:
            n, m = map(int, tokens[:2])
            edge_tokens = tokens[2:]
        edges = [(int(edge_tokens[i]), int(edge_tokens[i + 1])) for i in range(0, 2 * m, 2)]
        directed = operation == "topological"
        graph = [[] for _ in range(n)]
        for left, right in edges:
            graph[left].append(right)
            if not directed:
                graph[right].append(left)
        if operation == "graph_shortest":
            distances = [-1] * n
            distances[source] = 0
            queue = deque([source])
            while queue:
                node = queue.popleft()
                for neighbor in graph[node]:
                    if distances[neighbor] == -1:
                        distances[neighbor] = distances[node] + 1
                        queue.append(neighbor)
            result = str(distances[target])
        elif operation == "components":
            seen = set()
            count = 0
            for start in range(n):
                if start in seen:
                    continue
                count += 1
                stack = [start]
                seen.add(start)
                while stack:
                    for neighbor in graph[stack.pop()]:
                        if neighbor not in seen:
                            seen.add(neighbor)
                            stack.append(neighbor)
            result = str(count)
        elif operation == "topological":
            indegree = [0] * n
            for left, right in edges:
                indegree[right] += 1
            queue = deque(index for index, degree in enumerate(indegree) if degree == 0)
            visited = 0
            while queue:
                node = queue.popleft()
                visited += 1
                for neighbor in graph[node]:
                    indegree[neighbor] -= 1
                    if indegree[neighbor] == 0:
                        queue.append(neighbor)
            result = str(visited == n).lower()
        elif operation == "bipartite":
            colors = [-1] * n
            valid = True
            for start in range(n):
                if colors[start] != -1:
                    continue
                colors[start] = 0
                queue = deque([start])
                while queue and valid:
                    node = queue.popleft()
                    for neighbor in graph[node]:
                        if colors[neighbor] == -1:
                            colors[neighbor] = 1 - colors[node]
                            queue.append(neighbor)
                        elif colors[neighbor] == colors[node]:
                            valid = False
                            break
            result = str(valid).lower()
        else:
            result = str(max((len(neighbors) for neighbors in graph), default=0))
    elif operation == "islands":
        rows, columns = map(int, tokens[:2])
        grid = tokens[2:2 + rows]
        seen = set()
        islands = 0
        for row in range(rows):
            for column in range(columns):
                if grid[row][column] != "1" or (row, column) in seen:
                    continue
                islands += 1
                stack = [(row, column)]
                seen.add((row, column))
                while stack:
                    current_row, current_column = stack.pop()
                    for next_row, next_column in (
                        (current_row - 1, current_column),
                        (current_row + 1, current_column),
                        (current_row, current_column - 1),
                        (current_row, current_column + 1),
                    ):
                        if (
                            0 <= next_row < rows
                            and 0 <= next_column < columns
                            and grid[next_row][next_column] == "1"
                            and (next_row, next_column) not in seen
                        ):
                            seen.add((next_row, next_column))
                            stack.append((next_row, next_column))
        result = str(islands)
    else:
        raise ValueError(f"Unknown catalog operation: {operation}")

    return result + "\n"


CONTEST_SPECS = (
    ("Arrays & Strings Foundations", "Build fluency with arrays, prefixes, and string scans.", 60, (
        ("Two Sum Indices", "two_sum_indices"), ("Reverse Words", "reverse_words"), ("Valid Palindrome", "palindrome"), ("Prefix Totals", "prefix"),
        ("Maximum Subarray", "max_subarray"), ("Product Except Self", "product_except"), ("Longest Unique Substring", "longest_unique"),
        ("Target Frequency", "target_count"), ("Sorted Sequence Check", "sorted"), ("Rotate Array", "rotate"),
    )),
    ("Core Algorithms Sprint", "Practice searching, number theory, and dynamic programming.", 75, (
        ("Binary Search", "binary_search"), ("Maximum Subarray Sum", "max_subarray"), ("Merge Sorted Arrays", "merge_sorted"), ("Longest Increasing Subsequence", "lis"),
        ("Minimum Coin Change", "coin_change"), ("Subset Sum", "subset_sum"), ("Interval Scheduling", "intervals"), ("Fibonacci Number", "fibonacci"),
        ("Edit Distance", "edit_distance"), ("Grid Path Count", "grid_paths"),
    )),
    ("Interview Challenge Pack", "Tackle classic interview patterns and edge cases.", 75, (
        ("Valid Parentheses", "balanced"), ("Next Greater Element", "next_greater"), ("Two Sum Exists", "pair_sum"), ("Valid Anagram", "anagram"),
        ("Majority Element", "majority"), ("Longest Unique Substring", "longest_unique"), ("Product Except Self", "product_except"),
        ("Longest Consecutive Sequence", "longest_consecutive"), ("Subarray Sum Count", "subarray_count"), ("Top Frequent Values", "top_frequency"),
    )),
    ("Hashing & Frequency Lab", "Use sets and maps to turn repeated work into constant-time lookups.", 65, (
        ("Unique Badge Count", "distinct"), ("Inventory Target Count", "target_count"), ("Complement Pair", "pair_sum"), ("Signature Anagrams", "anagram"),
        ("Dominant Identifier", "majority"), ("First Unshared Symbol", "first_unique"), ("Shared Registry Values", "intersection"),
        ("Consecutive Run", "longest_consecutive"), ("Prefix Hash Subarrays", "subarray_count"), ("Frequency Leaderboard", "top_frequency"),
    )),
    ("Sliding Window Workshop", "Master fixed and variable windows over arrays and strings.", 70, (
        ("Best Fixed Window", "window_max_sum"), ("Smallest Target Window", "window_min_len"), ("Distinct Values Per Window", "window_distinct"),
        ("Longest Ones With Flips", "max_ones"), ("Anagram Window Count", "anagram_windows"), ("Unique Character Window", "longest_unique"),
        ("Window Target Frequency", "target_count"), ("Window Prefix Totals", "prefix"), ("Window Maximum Segment", "max_subarray"), ("Window Rotation Check", "rotate"),
    )),
    ("Stacks & Parsing Arena", "Parse nested structures and solve nearest-element problems with stacks.", 70, (
        ("Balanced Delimiters", "balanced"), ("Next Greater Signal", "next_greater"), ("Postfix Calculator", "postfix"), ("Parentheses Repair Count", "min_removals"),
        ("Largest Histogram Rectangle", "histogram"), ("Canonical Unix Path", "simplify_path"), ("Decode Repeated Text", "decode_repeat"),
        ("Reverse Stack Output", "reverse"), ("Stack Target Count", "target_count"), ("Nested Edit Distance", "edit_distance"),
    )),
    ("Search & Backtracking Quest", "Explore candidate spaces with pruning and careful state.", 80, (
        ("Search a Sorted Realm", "binary_search"), ("Subset Treasure", "subset_sum"), ("Permutation Count", "permutation_count"), ("Combination Sum Count", "combination_count"),
        ("Reach the Final Tile", "jump_game"), ("Grid Route Count", "grid_paths"), ("Increasing Trail", "lis"), ("Coin Combination Minimum", "coin_change"),
        ("Decode Search Tree", "decode_repeat"), ("Target Pair Search", "pair_sum"),
    )),
    ("Greedy Strategy Circuit", "Choose locally useful moves and prove when they form a global solution.", 75, (
        ("Maximum Compatible Meetings", "intervals"), ("Circular Fuel Route", "gas_station"), ("Assign Cookies", "assign_cookies"), ("Reachable Jump Path", "jump_game"),
        ("Greedy Coin Baseline", "coin_change"), ("Smallest Window Cover", "window_min_len"), ("Frequency Selection", "top_frequency"),
        ("Kth Ranked Candidate", "kth_smallest"), ("Knapsack Value", "knapsack"), ("Minimum Edit Plan", "edit_distance"),
    )),
    ("Dynamic Programming, Trees & Heaps", "Combine recurrence design with tree and priority-queue fundamentals.", 90, (
        ("Fibonacci Table", "fibonacci"), ("Grid Dynamic Paths", "grid_paths"), ("Coin Change Table", "coin_change"), ("Increasing Subsequence DP", "lis"),
        ("String Edit Table", "edit_distance"), ("Zero-One Knapsack", "knapsack"), ("Kth Heap Candidate", "kth_smallest"),
        ("Rooted Tree Height", "tree_height"), ("Rooted Tree Leaves", "tree_leaves"), ("Subset State Table", "subset_sum"),
    )),
    ("Graph Algorithms Expedition", "Traverse, classify, and reason about directed and undirected graphs.", 90, (
        ("Unweighted Shortest Route", "graph_shortest"), ("Connected Components", "components"), ("Directed Acyclic Check", "topological"), ("Bipartite Graph Check", "bipartite"),
        ("Grid Island Count", "islands"), ("Maximum Vertex Degree", "degree_max"), ("Graph Reachability Distance", "graph_shortest"),
        ("Forest Component Count", "components"), ("Dependency Cycle Check", "topological"), ("Odd Cycle Detection", "bipartite"),
    )),
)


def build_catalog() -> tuple[CatalogContest, ...]:
    contests = []
    for title, description, duration, problem_specs in CONTEST_SPECS:
        questions = []
        for index, (problem_title, operation) in enumerate(problem_specs):
            difficulty = (
                Difficulty.EASY
                if index < 4
                else Difficulty.MEDIUM
                if index < 8
                else Difficulty.HARD
            )
            cases = tuple(
                CatalogCase(
                    input_data=input_data,
                    output_data=solve_reference(operation, input_data),
                    is_hidden=case_index >= 2,
                )
                for case_index, input_data in enumerate(CASES[operation])
            )
            questions.append(
                CatalogQuestion(
                    title=problem_title,
                    description=OPERATION_DOCS[operation],
                    difficulty=difficulty,
                    cases=cases,
                )
            )
        contests.append(
            CatalogContest(
                title=title,
                description=description,
                duration=duration,
                questions=tuple(questions),
            )
        )
    return tuple(contests)


CATALOG = build_catalog()


def validate_catalog() -> None:
    assert len(CATALOG) == 10
    questions = [question for contest in CATALOG for question in contest.questions]
    assert len(questions) == 100
    assert Counter(question.difficulty for question in questions) == {
        Difficulty.EASY: 40,
        Difficulty.MEDIUM: 40,
        Difficulty.HARD: 20,
    }
    assert all(len(question.cases) == 5 for question in questions)
    assert all(sum(not case.is_hidden for case in question.cases) >= 2 for question in questions)
    assert all(sum(case.is_hidden for case in question.cases) >= 3 for question in questions)


validate_catalog()
