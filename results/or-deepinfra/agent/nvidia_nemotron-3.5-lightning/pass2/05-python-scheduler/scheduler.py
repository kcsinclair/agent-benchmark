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
    ends = [0.0] * (n + 1)
    # dp[k] = optimal weight using first k jobs (k from 0 to n)
    dp = [0.0] * (n + 1)
    # choice[k] = True if job k-1 is included in the optimal subset, else False
    choice = [False] * (n + 1)

    # Pre-extract sorted start, end, weight, original index for speed
    sorted_starts = [job[0] for job in indexed]
    sorted_ends = [job[1] for job in indexed]
    sorted_weights = [job[2] for job in indexed]
    sorted_orig_idx = [job[3] for job in indexed]

    for k in range(1, n + 1):
        s = sorted_starts[k - 1]
        e = sorted_ends[k - 1]
        w = sorted_weights[k - 1]

        # Find the number of jobs (in sorted order) that end <= s.
        # bisect_right returns count of elements <= s in ends[1..k-1].
        # We search in ends[1:k] (i.e. up to but not including current job).
        # Since ends is monotonic (sorted by end time), we can use bisect_right.
        # To keep O(1) access, we maintain ends up to k-1 already filled.
        # bisect_right on the whole list is fine; we just ignore indices >= k.
        # But to be safe, we search in ends[1:k] via custom logic:
        # We'll use bisect_right on the full ends list but with lo=1, hi=k.
        # However bisect_right doesn't support hi parameter directly in older Python,
        # so we just pass the slice conceptually. We'll implement manually.
        # Since ends is sorted, we can use bisect_right on ends with lo=1, hi=k.
        # Python's bisect.bisect_right accepts lo and hi.
        p = bisect_right(ends, s, 1, k)  # p is count of jobs among first k-1 that end <= s
        # dp index for that job is p (since dp is 1-indexed, dp[p] uses first p jobs)
        include_weight = dp[p] + w

        if include_weight > dp[k - 1]:
            dp[k] = include_weight
            choice[k] = True
        else:
            dp[k] = dp[k - 1]
            choice[k] = False

    # Reconstruct chosen indices
    chosen: list[int] = []
    k = n
    while k > 0:
        if choice[k]:
            # job k-1 (0-indexed in sorted) is included
            orig_idx = sorted_orig_idx[k - 1]
            chosen.append(orig_idx)
            # move to the prefix that is compatible: p jobs that end <= s
            # p was computed during the loop; we need to recompute or store it.
            # We'll recompute p using the same logic.
            s = sorted_starts[k - 1]
            # p is the number of jobs among first k-1 with end <= s
            p = bisect_right(ends, s, 1, k)
            k = p
        else:
            k -= 1

    # Sort chosen indices by start time, break ties by index ascending
    # We need start times for the chosen original indices; we can look them up from jobs.
    # To sort efficiently, we pair each chosen index with its start time.
    chosen_with_start = [(jobs[i][0], i) for i in chosen]
    chosen_with_start.sort(key=lambda x: (x[0], x[1]))
    chosen_sorted = [idx for _, idx in chosen_with_start]

    return (float(dp[n]), chosen_sorted)
