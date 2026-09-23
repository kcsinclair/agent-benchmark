from __future__ import annotations
from bisect import bisect_right


def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    """
    Weighted interval scheduling in O(n log n) time.

    Args:
        jobs: list of (start, end, weight) tuples.

    Returns:
        (total_weight, chosen_indices) where chosen_indices are indices into
        the input list, sorted by start time (ties broken by index ascending).
    """
    if not jobs:
        return (0.0, [])

    # Attach original index to each job
    indexed = [(s, e, w, i) for i, (s, e, w) in enumerate(jobs)]
    # Sort by end time, then by start time, then by original index for determinism
    indexed.sort(key=lambda x: (x[1], x[0], x[3]))

    n = len(indexed)
    # ends[k] = end time of the k-th job in sorted order (1-indexed for convenience)
    ends = [0] * (n + 1)
    # p[k] = largest index j < k such that job j ends <= start of job k (0-indexed concept)
    # We'll compute p for each sorted job (1-indexed)
    p = [0] * (n + 1)  # p[k] will be the count of jobs that can be scheduled before k

    # Build ends and compute p using binary search
    for k in range(1, n + 1):
        s, e, w, orig_idx = indexed[k - 1]
        ends[k] = e
        # Find the rightmost job in indexed[0..k-1] with end <= s
        # bisect_right on ends[1..k-1] gives count of jobs with end <= s
        # we search in ends[1:k] (indices 1 to k-1 inclusive)
        # equivalent to bisect_right(ends, s, 1, k) but hi=k means up to index k-1
        j = bisect_right(ends, s, 1, k)  # returns count of jobs with end <= s among first k-1 jobs
        p[k] = j

    # DP: dp[k] = optimal weight using first k jobs (sorted by end time)
    dp = [0.0] * (n + 1)
    # choice[k] = True if we include job k, False if we skip it
    choice = [False] * (n + 1)  # choice[k] indicates whether job k (1-indexed) is included in optimal

    for k in range(1, n + 1):
        s, e, w, orig_idx = indexed[k - 1]
        include = w + dp[p[k]]
        exclude = dp[k - 1]
        if include > exclude:
            dp[k] = include
            choice[k] = True
        else:
            dp[k] = exclude
            choice[k] = False

    # Reconstruct chosen jobs
    chosen_sorted: list[int] = []  # original indices of chosen jobs, in sorted-by-end order
    k = n
    while k > 0:
        if choice[k]:
            # job k (1-indexed) is chosen
            _, _, _, orig_idx = indexed[k - 1]
            chosen_sorted.append(orig_idx)
            k = p[k]
        else:
            k -= 1

    # chosen_sorted currently has original indices in reverse order of processing (by end time)
    # We need to return them sorted by start time, breaking ties by index ascending
    chosen_sorted.sort(key=lambda idx: (jobs[idx][0], idx))

    total_weight = dp[n]
    return (float(total_weight), chosen_sorted)


# Simple test harness
if __name__ == "__main__":
    import sys
    jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
    weight, idx = best_schedule(jobs)
    print(f"weight={weight}, indices={idx}")
    # Expected: (13.0, [2, 6])
