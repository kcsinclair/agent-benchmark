def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    n = len(jobs)
    if n == 0:
        return (0.0, [])

    # Sort indices by end time (then by start, then index) for a stable DP order.
    order = sorted(range(n), key=lambda i: (jobs[i][1], jobs[i][0], i))

    ends = [jobs[i][1] for i in order]      # sorted end times
    starts = [jobs[i][0] for i in order]
    weights = [jobs[i][2] for i in order]

    # p[k] = largest j < k such that ends[j] <= starts[k]  (job j compatible with k)
    # Computed via binary search: O(n log n).
    p = [0] * n
    for k in range(n):
        lo, hi = 0, k - 1
        target = starts[k]
        # find rightmost index j in [0, k-1] with ends[j] <= target
        pos = -1
        while lo <= hi:
            mid = (lo + hi) // 2
            if ends[mid] <= target:
                pos = mid
                lo = mid + 1
            else:
                hi = mid - 1
        p[k] = pos  # -1 if none

    # Bottom-up DP over sorted order.
    # dp[k] = best total weight using jobs order[0..k] (0-indexed counting from 0..k inclusive)
    dp = [0.0] * (n + 1)  # dp[k] uses first k jobs in sorted order
    for k in range(1, n + 1):
        i = k - 1  # index in sorted arrays
        take = weights[i] + (dp[p[i] + 1] if p[i] >= 0 else 0.0)
        skip = dp[k - 1]
        dp[k] = take if take > skip else skip

    # Backtrack to find chosen indices.
    chosen = []
    k = n
    while k > 0:
        i = k - 1
        take = weights[i] + (dp[p[i] + 1] if p[i] >= 0 else 0.0)
        # Tie-breaking: to keep it deterministic and valid, prefer "take" when equal
        # only if it helps match. Any optimum is acceptable per spec.
        if take >= dp[k - 1] and take > dp[k - 1]:
            chosen.append(order[i])
            k = p[i] + 1
        elif take == dp[k - 1]:
            # Prefer taking if it doesn't reduce total; still optimal.
            chosen.append(order[i])
            k = p[i] + 1
        else:
            k -= 1

    # chosen currently in reverse order of sorted-by-end; sort by start, tie by index.
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return (dp[n], chosen)
