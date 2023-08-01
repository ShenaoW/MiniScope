#!/usr/bin/env python
# -*- coding: utf-8 -*-


import re


def is_http_url(s):
    """
    判断字符串是否为一个 http url
    """
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        # domain...
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if regex.match(s):
        return True
    else:
        return False

def lcs(word1: str, word2: str) -> str:
    """
    最长公共子串

    @param word1: str
    @param word2: str
    :return: word1 和 word2 的最长公共子串
    """
    m = len(word1)
    n = len(word2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    max_len = 0
    row = 0
    col = 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if word1[i - 1] == word2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if max_len < dp[i][j]:
                    max_len = dp[i][j]
                    row = i
                    col = j

    max_str = ""
    i = row
    j = col
    while i > 0 and j > 0:
        if dp[i][j] == 0:
            break
        i -= 1
        j -= 1
        max_str += word1[i]

    lcstr = max_str[::-1]
    return lcstr

def levenshtein_distance(xpath1, xpath2):
    """Calculating Levenshtein Distance between two xpaths
    :param: xpath1
    :param: xpath2
    """

    # init 2d array
    rows = len(xpath1) + 1
    cols = len(xpath2) + 1
    dist = [[0 for j in range(cols)] for i in range(rows)]

    # init the first row
    for i in range(rows):
        dist[i][0] = i

    # init the first column
    for j in range(cols):
        dist[0][j] = j

    # dp
    for i in range(1, rows):
        for j in range(1, cols):
            cost = 0 if xpath1[i - 1] == xpath2[j - 1] else 1
            dist[i][j] = min(dist[i - 1][j] + 1,         # delete
                             dist[i][j - 1] + 1,         # insert
                             dist[i - 1][j - 1] + cost)  # replace

    # return the number in the bottom right corner
    return dist[rows - 1][cols - 1]