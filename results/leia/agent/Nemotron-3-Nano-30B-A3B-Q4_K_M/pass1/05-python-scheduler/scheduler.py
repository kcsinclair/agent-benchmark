import bisect
from typing import List, Tuple

def best_schedule(jobs: List[Tuple[float, float, float]]) -> Tuple[float, List[int]]:
    """
    Weighted interval scheduling with O(n log n) time.

    Parameters
    ----------
    jobs : list of (start, end, weight)
        Each job has a start time < end time and a positive weight.

    Returns
    -------
    (total_weight, chosen_indices)
        total_weight – maximum achievable sum of weights (float)
        chosen_indices – indices of the selected jobs, sorted by start time
                         (ties broken by original index ascending)
    """
    if not jobs:
        return (0.0, [])

    # Keep original indices and sort by end time
    indexed = [(s, e, w, idx) for idx, (s, e, w) in enumerate(jobs)]
    indexed.sort(key=lambda x: x[1])          # sort by end
    ends = [job[1] for job in indexed]        # list of end times for binary search
    n = len(indexed)

    # DP arrays
    dp = [0.0] * (n + 1)        # dp[i] = optimal weight for first i jobs (i = count)
    take = [False] * (n + 1)    # take[i] = True if job i-1 is taken in optimal solution

    # Fill DP
    for i in range(1, n + 1):
        s, e, w, _ = indexed[i - 1]
        # j = number of jobs that end <= s
        j = bisect.bisect_right(ends, s)
        include = w + dp[j]
        exclude = dp[i - 1]
        if include > exclude:
            dp[i] = include
            take[i] = True
        else:
            dp[i] = exclude
            take[i] = False

    # Reconstruct chosen indices
    chosen: List[int] = []
    i = n
    while i > 0:
        if take[i]:
            # job i-1 is selected
            chosen.append(indexed[i - 1][3])  # original index
            # jump to the last compatible job count
            s, _, _, _ = indexed[i - 1]
            j = bisect.bisect_right(ends, s)
            i = j
        else:
            i -= 1

    # Sort chosen indices by start time, then by original index
    chosen.sort(key=lambda idx: (jobs[idx][0], idx))

    return (float(dp[n]), chosen)
