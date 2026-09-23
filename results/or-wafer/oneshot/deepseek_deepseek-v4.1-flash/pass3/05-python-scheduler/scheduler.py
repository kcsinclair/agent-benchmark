"""
scheduler.py — Weighted interval scheduling, O(n log n).

Solves the classic maximum-weight non-overlapping interval selection problem.

Approach
--------
1. Sort jobs by end time.  Let the sorted order be `order`.
2. For each job in that order, compute p[i] = index (in sorted order) of the
   last job whose end time is <= the start time of job i, or -1 if none.
   Found by binary search.
3. DP:  M[i] = max(M[i-1],  weight[i] + M[p[i]])   where M[-1] = 0.
4. Backtrack through the DP table to recover one optimal set of jobs.

Touching intervals (end == start) are allowed, so the binary search uses
`bisect_right` on end times.

Time complexity:  O(n log n).  Space: O(n).
"""

from bisect import bisect_right


def best_schedule(jobs):
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort by end time; keep original index.  Ties broken by index so output
    # is deterministic (order of equal-end jobs does not affect optimum).
    order = sorted(range(n), key=lambda i: (jobs[i][1], i))

    ends = [jobs[i][1] for i in order]          # ends[k] = end time of k-th job
    starts_sorted = [jobs[i][0] for i in order]

    # p[k] = largest j < k such that ends[j] <= starts_sorted[k], else -1.
    # Since ends is non-decreasing (sort key), bisect works.
    p = [0] * n
    for k in range(n):
        # find rightmost position with ends[pos] <= starts_sorted[k]
        pos = bisect_right(ends, starts_sorted[k], 0, k) - 1
        p[k] = pos  # may be -1

    # DP forward.
    # M[k] = best total weight using jobs among order[0..k].
    # Use k+1 offset so M[k+1] corresponds to first k jobs; M[0] = 0.
    M = [0.0] * (n + 1)
    weights_sorted = [0.0] * n
    for k in range(n):
        weights_sorted[k] = jobs[order[k]][2]

    for k in range(n):
        w = weights_sorted[k]
        take = w + M[p[k] + 1]        # p[k]+1 maps -1 -> 0
        skip = M[k]                   # M[k] is best using first k jobs (0..k-1)
        M[k + 1] = take if take > skip else skip

    # Backtrack to recover chosen jobs (in sorted-order positions).
    chosen_positions = []
    k = n  # number of jobs considered so far (positions 0..k-1)
    while k > 0:
        idx_pos = k - 1
        w = weights_sorted[idx_pos]
        take = w + M[p[idx_pos] + 1]
        skip = M[k - 1]
        if take > skip:
            chosen_positions.append(idx_pos)
            k = p[idx_pos] + 1
        else:
            k -= 1

    # Map back to original indices.
    chosen = [order[pos] for pos in chosen_positions]
    # Sort by (start, index) as required.
    chosen.sort(key=lambda i: (jobs[i][0], i))

    return (M[n], chosen)
