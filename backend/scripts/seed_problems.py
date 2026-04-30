"""
Seed the problems table with 30 hand-curated DSA problems.
Run from the project root:
    python -m backend.scripts.seed_problems
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import aiosqlite
from backend.services.db import DATABASE_URL, init_db

PROBLEMS = [
    # ------------------------------------------------------------------
    # ARRAYS — easy
    # ------------------------------------------------------------------
    {
        "slug": "two-sum",
        "title": "Two Sum",
        "topic": "arrays",
        "difficulty": "easy",
        "function_name": "two_sum",
        "description": (
            "Given an array of integers `nums` and an integer `target`, "
            "return the indices of the two numbers that add up to `target`. "
            "You may assume exactly one solution exists and you may not use "
            "the same element twice."
        ),
        "constraints": ["2 <= nums.length <= 10^4", "-10^9 <= nums[i] <= 10^9", "Only one valid answer exists"],
        "examples": [
            {"input": "nums = [2,7,11,15], target = 9", "output": "[0,1]", "explanation": "nums[0] + nums[1] = 2 + 7 = 9"},
            {"input": "nums = [3,2,4], target = 6",     "output": "[1,2]", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"nums": [2, 7, 11, 15], "target": 9},  "expected_output": [0, 1], "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [3, 2, 4],      "target": 6},  "expected_output": [1, 2], "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [3, 3],          "target": 6},  "expected_output": [0, 1], "is_hidden": True,  "edge_case_label": "duplicate values"},
            {"input": {"nums": [1, 2, 3, 4, 5], "target": 9}, "expected_output": [3, 4], "is_hidden": True,  "edge_case_label": "last two"},
            {"input": {"nums": [-1, -2, -3, -4], "target": -6},"expected_output": [1, 3], "is_hidden": True, "edge_case_label": "negative numbers"},
            {"input": {"nums": [0, 4, 3, 0],   "target": 0},  "expected_output": [0, 3], "is_hidden": True,  "edge_case_label": "zeros"},
        ],
        "brute_force_hint": "Try all pairs — O(n²).",
        "optimal_hint": "Use a hash map to store complement → index as you iterate.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(n)",
        "follow_up_questions": ["What if the array is sorted?", "What if you need to return the values instead of indices?"],
        "source_tags": ["classic"],
    },
    {
        "slug": "best-time-to-buy-sell-stock",
        "title": "Best Time to Buy and Sell Stock",
        "topic": "arrays",
        "difficulty": "easy",
        "function_name": "max_profit",
        "description": (
            "Given an array `prices` where `prices[i]` is the price of a stock on day `i`, "
            "return the maximum profit from a single buy-sell transaction. Return 0 if no profit is possible."
        ),
        "constraints": ["1 <= prices.length <= 10^5", "0 <= prices[i] <= 10^4"],
        "examples": [
            {"input": "prices = [7,1,5,3,6,4]", "output": "5", "explanation": "Buy on day 2 (price=1), sell on day 5 (price=6)"},
            {"input": "prices = [7,6,4,3,1]",   "output": "0", "explanation": "No profitable transaction"},
        ],
        "test_cases": [
            {"input": {"prices": [7, 1, 5, 3, 6, 4]}, "expected_output": 5,  "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"prices": [7, 6, 4, 3, 1]},    "expected_output": 0,  "is_hidden": False, "edge_case_label": "decreasing"},
            {"input": {"prices": [1]},                 "expected_output": 0,  "is_hidden": True,  "edge_case_label": "single element"},
            {"input": {"prices": [1, 2]},              "expected_output": 1,  "is_hidden": True,  "edge_case_label": "two elements"},
            {"input": {"prices": [2, 1]},              "expected_output": 0,  "is_hidden": True,  "edge_case_label": "two elements descending"},
            {"input": {"prices": [3, 3, 3, 3]},        "expected_output": 0,  "is_hidden": True,  "edge_case_label": "all same"},
            {"input": {"prices": [1, 2, 3, 4, 5]},     "expected_output": 4,  "is_hidden": True,  "edge_case_label": "increasing"},
        ],
        "brute_force_hint": "Try every buy-sell pair — O(n²).",
        "optimal_hint": "Track the minimum price seen so far and the maximum profit achievable at each step.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["What if you could make multiple transactions?"],
        "source_tags": ["classic"],
    },
    {
        "slug": "contains-duplicate",
        "title": "Contains Duplicate",
        "topic": "arrays",
        "difficulty": "easy",
        "function_name": "contains_duplicate",
        "description": "Given an integer array `nums`, return `True` if any value appears at least twice, and `False` if every element is distinct.",
        "constraints": ["1 <= nums.length <= 10^5", "-10^9 <= nums[i] <= 10^9"],
        "examples": [
            {"input": "nums = [1,2,3,1]", "output": "True",  "explanation": "1 appears twice"},
            {"input": "nums = [1,2,3,4]", "output": "False", "explanation": "All distinct"},
        ],
        "test_cases": [
            {"input": {"nums": [1, 2, 3, 1]},    "expected_output": True,  "is_hidden": False, "edge_case_label": "basic duplicate"},
            {"input": {"nums": [1, 2, 3, 4]},    "expected_output": False, "is_hidden": False, "edge_case_label": "all distinct"},
            {"input": {"nums": [1]},              "expected_output": False, "is_hidden": True,  "edge_case_label": "single element"},
            {"input": {"nums": [1, 1]},           "expected_output": True,  "is_hidden": True,  "edge_case_label": "two identical"},
            {"input": {"nums": list(range(100))}, "expected_output": False, "is_hidden": True,  "edge_case_label": "large distinct"},
            {"input": {"nums": [0, -1, 0]},       "expected_output": True,  "is_hidden": True,  "edge_case_label": "zeros duplicate"},
        ],
        "brute_force_hint": "Compare every pair — O(n²).",
        "optimal_hint": "Use a set to track seen elements in one pass.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(n)",
        "follow_up_questions": ["Could you solve it in O(1) space (with a trade-off)?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # ARRAYS — medium
    # ------------------------------------------------------------------
    {
        "slug": "product-of-array-except-self",
        "title": "Product of Array Except Self",
        "topic": "arrays",
        "difficulty": "medium",
        "function_name": "product_except_self",
        "description": (
            "Given an integer array `nums`, return an array `answer` such that "
            "`answer[i]` is equal to the product of all elements of `nums` except `nums[i]`. "
            "You must solve it without using division and in O(n) time."
        ),
        "constraints": ["2 <= nums.length <= 10^5", "-30 <= nums[i] <= 30", "The product fits in a 32-bit integer"],
        "examples": [
            {"input": "nums = [1,2,3,4]", "output": "[24,12,8,6]", "explanation": ""},
            {"input": "nums = [-1,1,0,-3,3]", "output": "[0,0,9,0,0]", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"nums": [1, 2, 3, 4]},       "expected_output": [24, 12, 8, 6],  "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [-1, 1, 0, -3, 3]},  "expected_output": [0, 0, 9, 0, 0], "is_hidden": False, "edge_case_label": "with zero"},
            {"input": {"nums": [1, 1]},              "expected_output": [1, 1],           "is_hidden": True,  "edge_case_label": "two elements"},
            {"input": {"nums": [0, 0]},              "expected_output": [0, 0],           "is_hidden": True,  "edge_case_label": "two zeros"},
            {"input": {"nums": [2, 3, 4, 5]},        "expected_output": [60, 40, 30, 24], "is_hidden": True,  "edge_case_label": "no zeros"},
            {"input": {"nums": [-2, -3]},            "expected_output": [-3, -2],         "is_hidden": True,  "edge_case_label": "negative only"},
        ],
        "brute_force_hint": "For each index, multiply all other elements — O(n²).",
        "optimal_hint": "Use a prefix product array and a suffix product array, then multiply them together.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1) output array only",
        "follow_up_questions": ["Can you do it with O(1) extra space (excluding the output array)?"],
        "source_tags": ["classic"],
    },
    {
        "slug": "maximum-subarray",
        "title": "Maximum Subarray",
        "topic": "arrays",
        "difficulty": "medium",
        "function_name": "max_subarray",
        "description": (
            "Given an integer array `nums`, find the contiguous subarray with the largest sum and return its sum."
        ),
        "constraints": ["1 <= nums.length <= 10^5", "-10^4 <= nums[i] <= 10^4"],
        "examples": [
            {"input": "nums = [-2,1,-3,4,-1,2,1,-5,4]", "output": "6", "explanation": "[4,-1,2,1] has the largest sum = 6"},
            {"input": "nums = [1]",                       "output": "1", "explanation": ""},
            {"input": "nums = [5,4,-1,7,8]",             "output": "23","explanation": ""},
        ],
        "test_cases": [
            {"input": {"nums": [-2, 1, -3, 4, -1, 2, 1, -5, 4]}, "expected_output": 6,   "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [1]},                               "expected_output": 1,   "is_hidden": False, "edge_case_label": "single element"},
            {"input": {"nums": [5, 4, -1, 7, 8]},                 "expected_output": 23,  "is_hidden": False, "edge_case_label": "mostly positive"},
            {"input": {"nums": [-1, -2, -3]},                     "expected_output": -1,  "is_hidden": True,  "edge_case_label": "all negative"},
            {"input": {"nums": [0, 0, 0]},                        "expected_output": 0,   "is_hidden": True,  "edge_case_label": "all zeros"},
            {"input": {"nums": [-2, -1]},                         "expected_output": -1,  "is_hidden": True,  "edge_case_label": "two negatives"},
            {"input": {"nums": [1, -1, 1, -1, 1]},                "expected_output": 1,   "is_hidden": True,  "edge_case_label": "alternating"},
        ],
        "brute_force_hint": "Try all O(n²) subarrays and track the max sum.",
        "optimal_hint": "Kadane's algorithm: extend the current subarray or start fresh, whichever is larger.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["Can you also return the subarray indices, not just the sum?"],
        "source_tags": ["classic", "kadane"],
    },
    # ------------------------------------------------------------------
    # STRINGS — easy
    # ------------------------------------------------------------------
    {
        "slug": "valid-anagram",
        "title": "Valid Anagram",
        "topic": "strings",
        "difficulty": "easy",
        "function_name": "is_anagram",
        "description": (
            "Given two strings `s` and `t`, return `True` if `t` is an anagram of `s`, and `False` otherwise. "
            "An anagram uses all the original letters exactly once."
        ),
        "constraints": ["1 <= s.length, t.length <= 5 * 10^4", "s and t consist of lowercase English letters"],
        "examples": [
            {"input": 's = "anagram", t = "nagaram"', "output": "True",  "explanation": ""},
            {"input": 's = "rat",     t = "car"',     "output": "False", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"s": "anagram", "t": "nagaram"}, "expected_output": True,  "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"s": "rat",     "t": "car"},     "expected_output": False, "is_hidden": False, "edge_case_label": "basic false"},
            {"input": {"s": "a",       "t": "a"},       "expected_output": True,  "is_hidden": True,  "edge_case_label": "single char"},
            {"input": {"s": "a",       "t": "b"},       "expected_output": False, "is_hidden": True,  "edge_case_label": "single char false"},
            {"input": {"s": "ab",      "t": "a"},       "expected_output": False, "is_hidden": True,  "edge_case_label": "different length"},
            {"input": {"s": "aabbcc",  "t": "abcabc"},  "expected_output": True,  "is_hidden": True,  "edge_case_label": "repeated chars"},
            {"input": {"s": "aaaa",    "t": "aaab"},    "expected_output": False, "is_hidden": True,  "edge_case_label": "one char off"},
        ],
        "brute_force_hint": "Sort both strings and compare — O(n log n).",
        "optimal_hint": "Count character frequencies with a hash map or a 26-element array.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1) (fixed 26-char alphabet)",
        "follow_up_questions": ["What if the inputs contain Unicode characters?"],
        "source_tags": ["classic"],
    },
    {
        "slug": "valid-palindrome",
        "title": "Valid Palindrome",
        "topic": "strings",
        "difficulty": "easy",
        "function_name": "is_palindrome",
        "description": (
            "A phrase is a palindrome if, after converting all uppercase letters to lowercase "
            "and removing all non-alphanumeric characters, it reads the same forward and backward. "
            "Given a string `s`, return `True` if it is a palindrome, or `False` otherwise."
        ),
        "constraints": ["1 <= s.length <= 2 * 10^5", "s consists only of printable ASCII characters"],
        "examples": [
            {"input": 's = "A man, a plan, a canal: Panama"', "output": "True",  "explanation": '"amanaplanacanalpanama" is a palindrome'},
            {"input": 's = "race a car"',                     "output": "False", "explanation": '"raceacar" is not a palindrome'},
            {"input": 's = " "',                              "output": "True",  "explanation": "empty after filtering"},
        ],
        "test_cases": [
            {"input": {"s": "A man, a plan, a canal: Panama"}, "expected_output": True,  "is_hidden": False, "edge_case_label": "classic"},
            {"input": {"s": "race a car"},                      "expected_output": False, "is_hidden": False, "edge_case_label": "false"},
            {"input": {"s": " "},                               "expected_output": True,  "is_hidden": False, "edge_case_label": "empty after filter"},
            {"input": {"s": "a"},                               "expected_output": True,  "is_hidden": True,  "edge_case_label": "single char"},
            {"input": {"s": "0P"},                              "expected_output": False, "is_hidden": True,  "edge_case_label": "digit and char"},
            {"input": {"s": ".,"},                              "expected_output": True,  "is_hidden": True,  "edge_case_label": "all punctuation"},
            {"input": {"s": "ab_a"},                            "expected_output": True,  "is_hidden": True,  "edge_case_label": "underscore filtered"},
        ],
        "brute_force_hint": "Filter then reverse the string and compare.",
        "optimal_hint": "Two pointers from both ends, skipping non-alphanumeric characters.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["How would you handle Unicode (e.g., accented characters)?"],
        "source_tags": ["classic"],
    },
    {
        "slug": "longest-common-prefix",
        "title": "Longest Common Prefix",
        "topic": "strings",
        "difficulty": "easy",
        "function_name": "longest_common_prefix",
        "description": (
            "Write a function to find the longest common prefix string among an array of strings `strs`. "
            "Return an empty string if there is no common prefix."
        ),
        "constraints": ["1 <= strs.length <= 200", "0 <= strs[i].length <= 200", "strs[i] consists of only lowercase English letters"],
        "examples": [
            {"input": 'strs = ["flower","flow","flight"]', "output": '"fl"', "explanation": ""},
            {"input": 'strs = ["dog","racecar","car"]',    "output": '""',   "explanation": "No common prefix"},
        ],
        "test_cases": [
            {"input": {"strs": ["flower", "flow", "flight"]}, "expected_output": "fl",  "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"strs": ["dog", "racecar", "car"]},    "expected_output": "",    "is_hidden": False, "edge_case_label": "no prefix"},
            {"input": {"strs": ["a"]},                         "expected_output": "a",   "is_hidden": True,  "edge_case_label": "single string"},
            {"input": {"strs": ["", "a"]},                    "expected_output": "",    "is_hidden": True,  "edge_case_label": "empty string"},
            {"input": {"strs": ["abc", "abc", "abc"]},        "expected_output": "abc", "is_hidden": True,  "edge_case_label": "all identical"},
            {"input": {"strs": ["ab", "a"]},                  "expected_output": "a",   "is_hidden": True,  "edge_case_label": "prefix is shorter"},
        ],
        "brute_force_hint": "Sort the array and compare only first and last strings.",
        "optimal_hint": "Take the first string as reference, then shrink it while it's not a prefix of each subsequent string.",
        "optimal_time_complexity": "O(S) where S = total characters",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["How would a trie help if this operation is called frequently on the same set?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # STRINGS — medium
    # ------------------------------------------------------------------
    {
        "slug": "longest-substring-without-repeating",
        "title": "Longest Substring Without Repeating Characters",
        "topic": "strings",
        "difficulty": "medium",
        "function_name": "length_of_longest_substring",
        "description": (
            "Given a string `s`, find the length of the longest substring without repeating characters."
        ),
        "constraints": ["0 <= s.length <= 5 * 10^4", "s consists of English letters, digits, symbols, and spaces"],
        "examples": [
            {"input": 's = "abcabcbb"', "output": "3", "explanation": '"abc" has length 3'},
            {"input": 's = "bbbbb"',    "output": "1", "explanation": '"b"'},
            {"input": 's = "pwwkew"',   "output": "3", "explanation": '"wke"'},
        ],
        "test_cases": [
            {"input": {"s": "abcabcbb"}, "expected_output": 3, "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"s": "bbbbb"},    "expected_output": 1, "is_hidden": False, "edge_case_label": "all same"},
            {"input": {"s": "pwwkew"},   "expected_output": 3, "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"s": ""},         "expected_output": 0, "is_hidden": True,  "edge_case_label": "empty string"},
            {"input": {"s": " "},        "expected_output": 1, "is_hidden": True,  "edge_case_label": "single space"},
            {"input": {"s": "au"},       "expected_output": 2, "is_hidden": True,  "edge_case_label": "two distinct"},
            {"input": {"s": "dvdf"},     "expected_output": 3, "is_hidden": True,  "edge_case_label": "restart mid-window"},
            {"input": {"s": "abcdef"},   "expected_output": 6, "is_hidden": True,  "edge_case_label": "all distinct"},
        ],
        "brute_force_hint": "Check all O(n²) substrings for uniqueness.",
        "optimal_hint": "Sliding window with a set or hash map tracking last-seen index of each character.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(min(n, alphabet))",
        "follow_up_questions": ["What if you also need to return the substring itself?"],
        "source_tags": ["classic", "sliding-window"],
    },
    {
        "slug": "group-anagrams",
        "title": "Group Anagrams",
        "topic": "strings",
        "difficulty": "medium",
        "function_name": "group_anagrams",
        "description": (
            "Given an array of strings `strs`, group the anagrams together. "
            "You can return the answer in any order."
        ),
        "constraints": ["1 <= strs.length <= 10^4", "0 <= strs[i].length <= 100", "strs[i] consists of lowercase English letters"],
        "examples": [
            {"input": 'strs = ["eat","tea","tan","ate","nat","bat"]', "output": '[["bat"],["nat","tan"],["ate","eat","tea"]]', "explanation": ""},
            {"input": 'strs = [""]',  "output": '[[""]]', "explanation": ""},
            {"input": 'strs = ["a"]', "output": '[["a"]]', "explanation": ""},
        ],
        "test_cases": [
            {
                "input": {"strs": ["eat", "tea", "tan", "ate", "nat", "bat"]},
                "expected_output": [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]],
                "is_hidden": False, "edge_case_label": "basic",
            },
            {"input": {"strs": [""]},  "expected_output": [[""]], "is_hidden": False, "edge_case_label": "empty string"},
            {"input": {"strs": ["a"]}, "expected_output": [["a"]], "is_hidden": False, "edge_case_label": "single"},
            {"input": {"strs": ["ab", "ba", "abc", "bca", "cab"]}, "expected_output": [["ab", "ba"], ["abc", "bca", "cab"]], "is_hidden": True, "edge_case_label": "two groups"},
        ],
        "brute_force_hint": "Sort each string to get a canonical key and group by it.",
        "optimal_hint": "Use a tuple of character counts (26 ints) as the hash map key to avoid sorting.",
        "optimal_time_complexity": "O(n * k) where k is max string length",
        "optimal_space_complexity": "O(n * k)",
        "follow_up_questions": ["How would you scale this to billions of strings?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # DYNAMIC PROGRAMMING — easy
    # ------------------------------------------------------------------
    {
        "slug": "climbing-stairs",
        "title": "Climbing Stairs",
        "topic": "dynamic-programming",
        "difficulty": "easy",
        "function_name": "climb_stairs",
        "description": (
            "You are climbing a staircase with `n` steps. Each time you can climb 1 or 2 steps. "
            "In how many distinct ways can you climb to the top?"
        ),
        "constraints": ["1 <= n <= 45"],
        "examples": [
            {"input": "n = 2", "output": "2", "explanation": "1+1 or 2"},
            {"input": "n = 3", "output": "3", "explanation": "1+1+1, 1+2, 2+1"},
        ],
        "test_cases": [
            {"input": {"n": 1},  "expected_output": 1,   "is_hidden": False, "edge_case_label": "n=1"},
            {"input": {"n": 2},  "expected_output": 2,   "is_hidden": False, "edge_case_label": "n=2"},
            {"input": {"n": 3},  "expected_output": 3,   "is_hidden": False, "edge_case_label": "n=3"},
            {"input": {"n": 4},  "expected_output": 5,   "is_hidden": True,  "edge_case_label": "n=4"},
            {"input": {"n": 10}, "expected_output": 89,  "is_hidden": True,  "edge_case_label": "n=10"},
            {"input": {"n": 45}, "expected_output": 1836311903, "is_hidden": True, "edge_case_label": "max n"},
        ],
        "brute_force_hint": "Recursive solution — notice it recomputes the same subproblems.",
        "optimal_hint": "This is essentially Fibonacci: dp[i] = dp[i-1] + dp[i-2]. Use two variables instead of an array.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["What if you could climb 1, 2, or 3 steps?"],
        "source_tags": ["classic", "fibonacci"],
    },
    {
        "slug": "house-robber",
        "title": "House Robber",
        "topic": "dynamic-programming",
        "difficulty": "easy",
        "function_name": "rob",
        "description": (
            "You are a robber planning to rob houses along a street. Adjacent houses have security systems "
            "connected — if two adjacent houses are robbed, the police are alerted. "
            "Given an array `nums` representing money in each house, return the maximum amount you can rob tonight."
        ),
        "constraints": ["1 <= nums.length <= 100", "0 <= nums[i] <= 400"],
        "examples": [
            {"input": "nums = [1,2,3,1]", "output": "4", "explanation": "Rob house 1 (1) then house 3 (3)"},
            {"input": "nums = [2,7,9,3,1]","output": "12","explanation": "Rob house 1 (2), 3 (9), 5 (1)"},
        ],
        "test_cases": [
            {"input": {"nums": [1, 2, 3, 1]},    "expected_output": 4,  "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [2, 7, 9, 3, 1]}, "expected_output": 12, "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [1]},              "expected_output": 1,  "is_hidden": True,  "edge_case_label": "single house"},
            {"input": {"nums": [1, 2]},           "expected_output": 2,  "is_hidden": True,  "edge_case_label": "two houses"},
            {"input": {"nums": [0, 0, 0, 0]},     "expected_output": 0,  "is_hidden": True,  "edge_case_label": "all zeros"},
            {"input": {"nums": [400, 0, 400]},    "expected_output": 800,"is_hidden": True,  "edge_case_label": "skip middle"},
            {"input": {"nums": [2, 1, 1, 2]},     "expected_output": 4,  "is_hidden": True,  "edge_case_label": "even-index sum wins"},
        ],
        "brute_force_hint": "Try all subsets of non-adjacent houses — exponential.",
        "optimal_hint": "dp[i] = max(dp[i-1], dp[i-2] + nums[i]). Use two variables.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["What if the houses are arranged in a circle (House Robber II)?"],
        "source_tags": ["classic"],
    },
    {
        "slug": "min-cost-climbing-stairs",
        "title": "Min Cost Climbing Stairs",
        "topic": "dynamic-programming",
        "difficulty": "easy",
        "function_name": "min_cost_climbing_stairs",
        "description": (
            "You are given an integer array `cost` where `cost[i]` is the cost of the `i`-th step. "
            "Once you pay the cost, you can climb one or two steps. "
            "You can either start from index 0 or index 1. Return the minimum cost to reach the top."
        ),
        "constraints": ["2 <= cost.length <= 1000", "0 <= cost[i] <= 999"],
        "examples": [
            {"input": "cost = [10,15,20]",         "output": "15", "explanation": "Start at index 1, pay 15, jump to top"},
            {"input": "cost = [1,100,1,1,1,100,1,1,100,1]", "output": "6", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"cost": [10, 15, 20]},                         "expected_output": 15, "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"cost": [1, 100, 1, 1, 1, 100, 1, 1, 100, 1]},"expected_output": 6,  "is_hidden": False, "edge_case_label": "zigzag"},
            {"input": {"cost": [0, 0]},                               "expected_output": 0,  "is_hidden": True,  "edge_case_label": "zeros"},
            {"input": {"cost": [1, 2]},                               "expected_output": 1,  "is_hidden": True,  "edge_case_label": "two steps"},
            {"input": {"cost": [0, 1, 2, 3]},                        "expected_output": 2,  "is_hidden": True,  "edge_case_label": "ascending"},
        ],
        "brute_force_hint": "Recursion with memoization.",
        "optimal_hint": "dp[i] = cost[i] + min(dp[i-1], dp[i-2]). The answer is min(dp[-1], dp[-2]).",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["How does this differ from Climbing Stairs?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # DYNAMIC PROGRAMMING — medium
    # ------------------------------------------------------------------
    {
        "slug": "coin-change",
        "title": "Coin Change",
        "topic": "dynamic-programming",
        "difficulty": "medium",
        "function_name": "coin_change",
        "description": (
            "You are given an integer array `coins` representing coins of different denominations "
            "and an integer `amount`. Return the fewest number of coins needed to make up that amount. "
            "Return -1 if it is not possible."
        ),
        "constraints": ["1 <= coins.length <= 12", "1 <= coins[i] <= 2^31 - 1", "0 <= amount <= 10^4"],
        "examples": [
            {"input": "coins = [1,2,5], amount = 11", "output": "3",  "explanation": "5+5+1"},
            {"input": "coins = [2], amount = 3",       "output": "-1", "explanation": "Cannot make 3"},
            {"input": "coins = [1], amount = 0",       "output": "0",  "explanation": ""},
        ],
        "test_cases": [
            {"input": {"coins": [1, 2, 5], "amount": 11}, "expected_output": 3,  "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"coins": [2],        "amount": 3},  "expected_output": -1, "is_hidden": False, "edge_case_label": "impossible"},
            {"input": {"coins": [1],        "amount": 0},  "expected_output": 0,  "is_hidden": False, "edge_case_label": "zero amount"},
            {"input": {"coins": [1],        "amount": 1},  "expected_output": 1,  "is_hidden": True,  "edge_case_label": "single coin"},
            {"input": {"coins": [1],        "amount": 2},  "expected_output": 2,  "is_hidden": True,  "edge_case_label": "multiple same"},
            {"input": {"coins": [186, 419, 83, 408], "amount": 6249}, "expected_output": 20, "is_hidden": True, "edge_case_label": "large amount"},
        ],
        "brute_force_hint": "Recursive DFS over all coin choices — exponential.",
        "optimal_hint": "Bottom-up DP: dp[i] = min(dp[i - c] + 1) for each coin c. Initialize dp[0]=0, rest=infinity.",
        "optimal_time_complexity": "O(amount * len(coins))",
        "optimal_space_complexity": "O(amount)",
        "follow_up_questions": ["What if you had unlimited coins of each denomination?", "How does this change if coins can only be used once?"],
        "source_tags": ["classic"],
    },
    {
        "slug": "longest-increasing-subsequence",
        "title": "Longest Increasing Subsequence",
        "topic": "dynamic-programming",
        "difficulty": "medium",
        "function_name": "length_of_lis",
        "description": (
            "Given an integer array `nums`, return the length of the longest strictly increasing subsequence."
        ),
        "constraints": ["1 <= nums.length <= 2500", "-10^4 <= nums[i] <= 10^4"],
        "examples": [
            {"input": "nums = [10,9,2,5,3,7,101,18]", "output": "4", "explanation": "[2,3,7,101]"},
            {"input": "nums = [0,1,0,3,2,3]",          "output": "4", "explanation": ""},
            {"input": "nums = [7,7,7,7]",              "output": "1", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"nums": [10, 9, 2, 5, 3, 7, 101, 18]}, "expected_output": 4, "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [0, 1, 0, 3, 2, 3]},           "expected_output": 4, "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [7, 7, 7, 7]},                 "expected_output": 1, "is_hidden": False, "edge_case_label": "all same"},
            {"input": {"nums": [1]},                          "expected_output": 1, "is_hidden": True,  "edge_case_label": "single"},
            {"input": {"nums": [1, 2, 3, 4, 5]},             "expected_output": 5, "is_hidden": True,  "edge_case_label": "strictly increasing"},
            {"input": {"nums": [5, 4, 3, 2, 1]},             "expected_output": 1, "is_hidden": True,  "edge_case_label": "strictly decreasing"},
        ],
        "brute_force_hint": "O(n²) DP: dp[i] = longest subsequence ending at i.",
        "optimal_hint": "Patience sorting / binary search approach: maintain a sorted list and use bisect_left — O(n log n).",
        "optimal_time_complexity": "O(n log n)",
        "optimal_space_complexity": "O(n)",
        "follow_up_questions": ["Can you reconstruct the actual subsequence, not just its length?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # TREES — easy
    # ------------------------------------------------------------------
    {
        "slug": "maximum-depth-binary-tree",
        "title": "Maximum Depth of Binary Tree",
        "topic": "trees",
        "difficulty": "easy",
        "function_name": "max_depth",
        "description": (
            "Given the root of a binary tree (as a nested list where each node is "
            "[val, left, right] and None represents a missing child), return its maximum depth. "
            "Maximum depth is the number of nodes along the longest path from root to leaf."
        ),
        "constraints": ["0 <= number of nodes <= 10^4", "-100 <= Node.val <= 100"],
        "examples": [
            {"input": "root = [3,9,20,null,null,15,7]", "output": "3", "explanation": ""},
            {"input": "root = [1,null,2]",               "output": "2", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"root": [3, [9, None, None], [20, [15, None, None], [7, None, None]]]}, "expected_output": 3, "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"root": [1, None, [2, None, None]]},                                    "expected_output": 2, "is_hidden": False, "edge_case_label": "right skewed"},
            {"input": {"root": None},                                                           "expected_output": 0, "is_hidden": True,  "edge_case_label": "empty tree"},
            {"input": {"root": [1, None, None]},                                               "expected_output": 1, "is_hidden": True,  "edge_case_label": "single node"},
            {"input": {"root": [1, [2, [3, [4, None, None], None], None], None]},             "expected_output": 4, "is_hidden": True,  "edge_case_label": "left skewed"},
        ],
        "brute_force_hint": "Recursive DFS: depth = 1 + max(left depth, right depth).",
        "optimal_hint": "The recursive solution is already optimal. Iterative BFS with a queue also works.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(h) where h is height",
        "follow_up_questions": ["How would you solve this iteratively using a queue?"],
        "source_tags": ["classic"],
    },
    {
        "slug": "invert-binary-tree",
        "title": "Invert Binary Tree",
        "topic": "trees",
        "difficulty": "easy",
        "function_name": "invert_tree",
        "description": (
            "Given the root of a binary tree (nested list [val, left, right], None for missing), "
            "invert the tree (mirror it) and return its root in the same nested list format."
        ),
        "constraints": ["0 <= number of nodes <= 100", "-100 <= Node.val <= 100"],
        "examples": [
            {"input": "root = [4,2,7,1,3,6,9]", "output": "[4,7,2,9,6,3,1]", "explanation": ""},
            {"input": "root = [2,1,3]",           "output": "[2,3,1]",         "explanation": ""},
        ],
        "test_cases": [
            {"input": {"root": [4, [2, [1, None, None], [3, None, None]], [7, [6, None, None], [9, None, None]]]},
             "expected_output": [4, [7, [9, None, None], [6, None, None]], [2, [3, None, None], [1, None, None]]],
             "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"root": None},                "expected_output": None, "is_hidden": True, "edge_case_label": "empty"},
            {"input": {"root": [1, None, None]},     "expected_output": [1, None, None], "is_hidden": True, "edge_case_label": "single"},
        ],
        "brute_force_hint": "Swap left and right children at each node recursively.",
        "optimal_hint": "The recursive swap is already optimal. Can also do iteratively with a queue.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(h)",
        "follow_up_questions": ["Can you do this iteratively?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # SLIDING WINDOW — medium
    # ------------------------------------------------------------------
    {
        "slug": "minimum-window-substring",
        "title": "Minimum Window Substring",
        "topic": "sliding-window",
        "difficulty": "medium",
        "function_name": "min_window",
        "description": (
            "Given strings `s` and `t`, return the minimum window substring of `s` "
            "that contains all characters of `t` (including duplicates). "
            "Return an empty string if no such window exists."
        ),
        "constraints": ["1 <= s.length, t.length <= 10^5", "s and t consist of uppercase and lowercase English letters"],
        "examples": [
            {"input": 's = "ADOBECODEBANC", t = "ABC"', "output": '"BANC"', "explanation": ""},
            {"input": 's = "a", t = "a"',               "output": '"a"',    "explanation": ""},
            {"input": 's = "a", t = "aa"',              "output": '""',     "explanation": ""},
        ],
        "test_cases": [
            {"input": {"s": "ADOBECODEBANC", "t": "ABC"}, "expected_output": "BANC", "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"s": "a",             "t": "a"},   "expected_output": "a",    "is_hidden": False, "edge_case_label": "single match"},
            {"input": {"s": "a",             "t": "aa"},  "expected_output": "",     "is_hidden": False, "edge_case_label": "impossible"},
            {"input": {"s": "abc",           "t": "abc"}, "expected_output": "abc",  "is_hidden": True,  "edge_case_label": "full string"},
            {"input": {"s": "bbaa",          "t": "aba"}, "expected_output": "baa",  "is_hidden": True,  "edge_case_label": "duplicates in t"},
        ],
        "brute_force_hint": "Check all O(n²) substrings and verify each contains all chars of t.",
        "optimal_hint": "Sliding window with two frequency maps. Shrink the window from the left when all chars are covered.",
        "optimal_time_complexity": "O(|s| + |t|)",
        "optimal_space_complexity": "O(|t|)",
        "follow_up_questions": ["What if t can contain non-ASCII characters?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # BINARY SEARCH — easy
    # ------------------------------------------------------------------
    {
        "slug": "binary-search",
        "title": "Binary Search",
        "topic": "binary-search",
        "difficulty": "easy",
        "function_name": "binary_search",
        "description": (
            "Given a sorted array of distinct integers `nums` and a target value `target`, "
            "return the index of `target`, or -1 if it does not exist."
        ),
        "constraints": ["1 <= nums.length <= 10^4", "-10^4 <= nums[i], target <= 10^4", "All values in nums are distinct and sorted in ascending order"],
        "examples": [
            {"input": "nums = [-1,0,3,5,9,12], target = 9",  "output": "4",  "explanation": "9 is at index 4"},
            {"input": "nums = [-1,0,3,5,9,12], target = 2",  "output": "-1", "explanation": "2 does not exist"},
        ],
        "test_cases": [
            {"input": {"nums": [-1, 0, 3, 5, 9, 12], "target": 9},  "expected_output": 4,  "is_hidden": False, "edge_case_label": "found"},
            {"input": {"nums": [-1, 0, 3, 5, 9, 12], "target": 2},  "expected_output": -1, "is_hidden": False, "edge_case_label": "not found"},
            {"input": {"nums": [5],                  "target": 5},  "expected_output": 0,  "is_hidden": True,  "edge_case_label": "single element found"},
            {"input": {"nums": [5],                  "target": 3},  "expected_output": -1, "is_hidden": True,  "edge_case_label": "single element not found"},
            {"input": {"nums": [1, 2, 3, 4, 5],     "target": 1},  "expected_output": 0,  "is_hidden": True,  "edge_case_label": "leftmost"},
            {"input": {"nums": [1, 2, 3, 4, 5],     "target": 5},  "expected_output": 4,  "is_hidden": True,  "edge_case_label": "rightmost"},
        ],
        "brute_force_hint": "Linear scan — O(n).",
        "optimal_hint": "Maintain lo and hi pointers. Check mid = (lo + hi) // 2 each step.",
        "optimal_time_complexity": "O(log n)",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["Why use (lo + hi) // 2 instead of (lo + hi) / 2? What about integer overflow?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # GRAPHS — medium
    # ------------------------------------------------------------------
    {
        "slug": "number-of-islands",
        "title": "Number of Islands",
        "topic": "graphs",
        "difficulty": "medium",
        "function_name": "num_islands",
        "description": (
            "Given an m×n grid of '1's (land) and '0's (water), count the number of islands. "
            "An island is surrounded by water and is formed by connecting adjacent lands horizontally or vertically."
        ),
        "constraints": ["1 <= m, n <= 300", "grid[i][j] is '0' or '1'"],
        "examples": [
            {"input": 'grid = [["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]', "output": "1", "explanation": ""},
            {"input": 'grid = [["1","1","0","0","0"],["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]]', "output": "3", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"grid": [["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]]}, "expected_output": 1, "is_hidden": False, "edge_case_label": "one island"},
            {"input": {"grid": [["1","1","0","0","0"],["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]]}, "expected_output": 3, "is_hidden": False, "edge_case_label": "three islands"},
            {"input": {"grid": [["0"]]},                                                                                  "expected_output": 0, "is_hidden": True,  "edge_case_label": "all water"},
            {"input": {"grid": [["1"]]},                                                                                  "expected_output": 1, "is_hidden": True,  "edge_case_label": "single land"},
            {"input": {"grid": [["1","0","1"],["0","1","0"],["1","0","1"]]},                                              "expected_output": 5, "is_hidden": True,  "edge_case_label": "checkerboard"},
        ],
        "brute_force_hint": "Iterate each cell; when you find a '1', DFS/BFS to mark all connected land.",
        "optimal_hint": "DFS or BFS marking visited cells in-place by setting '1' to '0'. Union-Find also works.",
        "optimal_time_complexity": "O(m * n)",
        "optimal_space_complexity": "O(m * n) worst case for DFS stack",
        "follow_up_questions": ["How would you count islands in a stream of data instead of a grid?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # LINKED LISTS — easy
    # ------------------------------------------------------------------
    {
        "slug": "reverse-linked-list",
        "title": "Reverse Linked List",
        "topic": "linked-lists",
        "difficulty": "easy",
        "function_name": "reverse_list",
        "description": (
            "Given the head of a singly linked list as a Python list `nodes`, "
            "return the reversed list."
        ),
        "constraints": ["0 <= number of nodes <= 5000", "-5000 <= Node.val <= 5000"],
        "examples": [
            {"input": "nodes = [1,2,3,4,5]", "output": "[5,4,3,2,1]", "explanation": ""},
            {"input": "nodes = [1,2]",        "output": "[2,1]",       "explanation": ""},
            {"input": "nodes = []",           "output": "[]",          "explanation": ""},
        ],
        "test_cases": [
            {"input": {"nodes": [1, 2, 3, 4, 5]}, "expected_output": [5, 4, 3, 2, 1], "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nodes": [1, 2]},           "expected_output": [2, 1],           "is_hidden": False, "edge_case_label": "two nodes"},
            {"input": {"nodes": []},               "expected_output": [],               "is_hidden": False, "edge_case_label": "empty"},
            {"input": {"nodes": [1]},              "expected_output": [1],              "is_hidden": True,  "edge_case_label": "single node"},
            {"input": {"nodes": list(range(10))},  "expected_output": list(range(9,-1,-1)), "is_hidden": True, "edge_case_label": "ten nodes"},
        ],
        "brute_force_hint": "Collect values into an array and return reversed.",
        "optimal_hint": "Three-pointer approach (prev, curr, next) in a single pass — O(1) space.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(1)",
        "follow_up_questions": ["Can you do this recursively?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # STACK / QUEUE — easy
    # ------------------------------------------------------------------
    {
        "slug": "valid-parentheses",
        "title": "Valid Parentheses",
        "topic": "stack-queue",
        "difficulty": "easy",
        "function_name": "is_valid",
        "description": (
            "Given a string `s` containing only '(', ')', '{', '}', '[', ']', "
            "determine if the input string is valid. "
            "An input string is valid if brackets are closed in the correct order and type."
        ),
        "constraints": ["1 <= s.length <= 10^4", "s consists of parentheses only '()[]{}'"],
        "examples": [
            {"input": 's = "()"',    "output": "True",  "explanation": ""},
            {"input": 's = "()[]{}"',"output": "True",  "explanation": ""},
            {"input": 's = "(]"',    "output": "False", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"s": "()"},     "expected_output": True,  "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"s": "()[]{}"},"expected_output": True,  "is_hidden": False, "edge_case_label": "mixed"},
            {"input": {"s": "(]"},     "expected_output": False, "is_hidden": False, "edge_case_label": "mismatched"},
            {"input": {"s": "([)]"},   "expected_output": False, "is_hidden": True,  "edge_case_label": "interleaved"},
            {"input": {"s": "{[]}"},   "expected_output": True,  "is_hidden": True,  "edge_case_label": "nested"},
            {"input": {"s": "]"},      "expected_output": False, "is_hidden": True,  "edge_case_label": "close only"},
            {"input": {"s": "("},      "expected_output": False, "is_hidden": True,  "edge_case_label": "open only"},
            {"input": {"s": "(((("},   "expected_output": False, "is_hidden": True,  "edge_case_label": "all open"},
        ],
        "brute_force_hint": "Repeatedly remove matching pairs until nothing changes.",
        "optimal_hint": "Stack: push open brackets, pop and verify on close brackets.",
        "optimal_time_complexity": "O(n)",
        "optimal_space_complexity": "O(n)",
        "follow_up_questions": ["How would you handle a wildcard '*' that can be '(', ')', or empty?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # HEAPS — medium
    # ------------------------------------------------------------------
    {
        "slug": "kth-largest-element",
        "title": "Kth Largest Element in an Array",
        "topic": "heaps",
        "difficulty": "medium",
        "function_name": "find_kth_largest",
        "description": (
            "Given an integer array `nums` and an integer `k`, return the `k`-th largest element. "
            "Note that it is the k-th largest in sorted order, not the k-th distinct element."
        ),
        "constraints": ["1 <= k <= nums.length <= 10^4", "-10^4 <= nums[i] <= 10^4"],
        "examples": [
            {"input": "nums = [3,2,1,5,6,4], k = 2", "output": "5", "explanation": ""},
            {"input": "nums = [3,2,3,1,2,4,5,5,6], k = 4", "output": "4", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"nums": [3, 2, 1, 5, 6, 4],       "k": 2}, "expected_output": 5, "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"nums": [3, 2, 3, 1, 2, 4, 5, 5, 6], "k": 4}, "expected_output": 4, "is_hidden": False, "edge_case_label": "duplicates"},
            {"input": {"nums": [1],                        "k": 1}, "expected_output": 1, "is_hidden": True,  "edge_case_label": "single element"},
            {"input": {"nums": [2, 1],                    "k": 1}, "expected_output": 2, "is_hidden": True,  "edge_case_label": "two elements"},
            {"input": {"nums": [2, 1],                    "k": 2}, "expected_output": 1, "is_hidden": True,  "edge_case_label": "kth is last"},
            {"input": {"nums": [-1, -1],                  "k": 1}, "expected_output": -1, "is_hidden": True, "edge_case_label": "negatives"},
        ],
        "brute_force_hint": "Sort descending and return index k-1 — O(n log n).",
        "optimal_hint": "Min-heap of size k: push elements, pop when size exceeds k. The top is the answer — O(n log k).",
        "optimal_time_complexity": "O(n log k)",
        "optimal_space_complexity": "O(k)",
        "follow_up_questions": ["Can you do this in O(n) average with QuickSelect?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # BACKTRACKING — medium
    # ------------------------------------------------------------------
    {
        "slug": "subsets",
        "title": "Subsets",
        "topic": "backtracking",
        "difficulty": "medium",
        "function_name": "subsets",
        "description": (
            "Given an integer array `nums` of unique elements, return all possible subsets (the power set). "
            "The solution set must not contain duplicate subsets. Return in any order."
        ),
        "constraints": ["1 <= nums.length <= 10", "-10 <= nums[i] <= 10", "All numbers in nums are unique"],
        "examples": [
            {"input": "nums = [1,2,3]", "output": "[[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]", "explanation": ""},
            {"input": "nums = [0]",     "output": "[[],[0]]", "explanation": ""},
        ],
        "test_cases": [
            {
                "input": {"nums": [1, 2, 3]},
                "expected_output": [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]],
                "is_hidden": False, "edge_case_label": "basic",
            },
            {"input": {"nums": [0]}, "expected_output": [[], [0]], "is_hidden": False, "edge_case_label": "single"},
        ],
        "brute_force_hint": "Backtracking: at each index, choose to include or exclude the element.",
        "optimal_hint": "Iterative bit mask: iterate 0 to 2^n, each bit represents include/exclude.",
        "optimal_time_complexity": "O(n * 2^n)",
        "optimal_space_complexity": "O(n * 2^n)",
        "follow_up_questions": ["How would you handle duplicates in the input array?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # TRIES — medium
    # ------------------------------------------------------------------
    {
        "slug": "implement-trie",
        "title": "Implement Trie (Prefix Tree)",
        "topic": "tries",
        "difficulty": "medium",
        "function_name": "trie_operations",
        "description": (
            "Implement a trie that supports insert, search, and startsWith operations. "
            "Given a list of operations `ops` and corresponding arguments `args`, "
            "return a list of results (None for insert, bool for search/startsWith)."
        ),
        "constraints": ["1 <= word.length, prefix.length <= 2000", "word and prefix consist of lowercase English letters", "At most 3 * 10^4 operations"],
        "examples": [
            {"input": 'ops = ["insert","search","search","startsWith","insert","search"], args = [["apple"],["apple"],["app"],["app"],["app"],["app"]]',
             "output": "[None,True,False,True,None,True]", "explanation": ""},
        ],
        "test_cases": [
            {
                "input": {
                    "ops": ["insert", "search", "search", "startsWith", "insert", "search"],
                    "args": [["apple"], ["apple"], ["app"], ["app"], ["app"], ["app"]],
                },
                "expected_output": [None, True, False, True, None, True],
                "is_hidden": False, "edge_case_label": "basic",
            },
            {
                "input": {
                    "ops": ["insert", "search", "startsWith"],
                    "args": [["a"], ["a"], ["a"]],
                },
                "expected_output": [None, True, True],
                "is_hidden": True, "edge_case_label": "single char",
            },
        ],
        "brute_force_hint": "Use a set for search and iterate set contents for startsWith — O(n) per query.",
        "optimal_hint": "Each TrieNode holds a dict of children and an is_end flag.",
        "optimal_time_complexity": "O(m) per operation where m is word length",
        "optimal_space_complexity": "O(total characters inserted)",
        "follow_up_questions": ["How would you add a delete operation?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # DYNAMIC PROGRAMMING — hard
    # ------------------------------------------------------------------
    {
        "slug": "word-break",
        "title": "Word Break",
        "topic": "dynamic-programming",
        "difficulty": "hard",
        "function_name": "word_break",
        "description": (
            "Given a string `s` and a list of strings `wordDict`, return `True` if `s` can be segmented "
            "into a space-separated sequence of one or more dictionary words."
        ),
        "constraints": ["1 <= s.length <= 300", "1 <= wordDict.length <= 1000", "1 <= wordDict[i].length <= 20"],
        "examples": [
            {"input": 's = "leetcode", wordDict = ["leet","code"]',              "output": "True",  "explanation": '"leet code"'},
            {"input": 's = "applepenapple", wordDict = ["apple","pen"]',         "output": "True",  "explanation": '"apple pen apple"'},
            {"input": 's = "catsandog", wordDict = ["cats","dog","sand","and"]', "output": "False", "explanation": ""},
        ],
        "test_cases": [
            {"input": {"s": "leetcode",     "wordDict": ["leet", "code"]},             "expected_output": True,  "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"s": "applepenapple","wordDict": ["apple", "pen"]},             "expected_output": True,  "is_hidden": False, "edge_case_label": "reuse word"},
            {"input": {"s": "catsandog",    "wordDict": ["cats", "dog", "sand", "and"]},"expected_output": False, "is_hidden": False, "edge_case_label": "impossible"},
            {"input": {"s": "a",            "wordDict": ["a"]},                        "expected_output": True,  "is_hidden": True,  "edge_case_label": "single char"},
            {"input": {"s": "ab",           "wordDict": ["a", "b"]},                  "expected_output": True,  "is_hidden": True,  "edge_case_label": "two single chars"},
            {"input": {"s": "aaaaaaa",      "wordDict": ["aaaa", "aaa"]},             "expected_output": True,  "is_hidden": True,  "edge_case_label": "overlapping"},
        ],
        "brute_force_hint": "Recursive DFS over all possible splits — exponential without memoization.",
        "optimal_hint": "dp[i] = True if s[:i] can be segmented. For each i, check all j < i where dp[j] is True and s[j:i] is in the word set.",
        "optimal_time_complexity": "O(n²)",
        "optimal_space_complexity": "O(n)",
        "follow_up_questions": ["How would you return all possible segmentations, not just True/False?"],
        "source_tags": ["classic"],
    },
    # ------------------------------------------------------------------
    # GRAPHS — hard
    # ------------------------------------------------------------------
    {
        "slug": "course-schedule-ii",
        "title": "Course Schedule II",
        "topic": "graphs",
        "difficulty": "hard",
        "function_name": "find_order",
        "description": (
            "There are `numCourses` courses labeled 0 to numCourses-1. "
            "You are given an array `prerequisites` where prerequisites[i] = [a, b] means you must take course b first. "
            "Return a valid ordering in which all courses can be finished, or an empty list if impossible."
        ),
        "constraints": ["1 <= numCourses <= 2000", "0 <= prerequisites.length <= numCourses * (numCourses - 1)", "prerequisites[i].length == 2"],
        "examples": [
            {"input": "numCourses = 2, prerequisites = [[1,0]]",         "output": "[0,1]",   "explanation": "Take 0 first"},
            {"input": "numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]", "output": "[0,2,1,3]", "explanation": ""},
            {"input": "numCourses = 1, prerequisites = []",              "output": "[0]",     "explanation": ""},
        ],
        "test_cases": [
            {"input": {"numCourses": 2, "prerequisites": [[1, 0]]},                     "expected_output": [0, 1],      "is_hidden": False, "edge_case_label": "basic"},
            {"input": {"numCourses": 1, "prerequisites": []},                           "expected_output": [0],         "is_hidden": False, "edge_case_label": "single course"},
            {"input": {"numCourses": 2, "prerequisites": [[1, 0], [0, 1]]},             "expected_output": [],          "is_hidden": True,  "edge_case_label": "cycle"},
            {"input": {"numCourses": 3, "prerequisites": [[1, 0], [2, 1]]},             "expected_output": [0, 1, 2],   "is_hidden": True,  "edge_case_label": "chain"},
        ],
        "brute_force_hint": "DFS cycle detection + topological sort.",
        "optimal_hint": "Kahn's algorithm (BFS with in-degree tracking): iteratively remove nodes with in-degree 0.",
        "optimal_time_complexity": "O(V + E)",
        "optimal_space_complexity": "O(V + E)",
        "follow_up_questions": ["What if you only need to know if the schedule is possible, not the order?"],
        "source_tags": ["classic", "topological-sort"],
    },
]


async def seed():
    await init_db()
    async with aiosqlite.connect(DATABASE_URL) as conn:
        inserted = 0
        skipped = 0
        for p in PROBLEMS:
            row = await conn.execute("SELECT id FROM problems WHERE slug = ?", (p["slug"],))
            if await row.fetchone():
                skipped += 1
                continue
            await conn.execute(
                """
                INSERT INTO problems
                    (slug, title, topic, difficulty, function_name, description,
                     constraints, examples, test_cases, brute_force_hint, optimal_hint,
                     optimal_time_complexity, optimal_space_complexity,
                     follow_up_questions, source_tags)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    p["slug"], p["title"], p["topic"], p["difficulty"],
                    p["function_name"], p["description"],
                    json.dumps(p["constraints"]),
                    json.dumps(p["examples"]),
                    json.dumps(p["test_cases"]),
                    p["brute_force_hint"], p["optimal_hint"],
                    p["optimal_time_complexity"], p["optimal_space_complexity"],
                    json.dumps(p["follow_up_questions"]),
                    json.dumps(p["source_tags"]),
                ),
            )
            inserted += 1
        await conn.commit()
        print(f"Seeded {inserted} problems, skipped {skipped} already-existing.")


if __name__ == "__main__":
    asyncio.run(seed())
