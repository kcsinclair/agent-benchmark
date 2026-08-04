# Problem 5 — Weighted Interval Scheduling at Scale (Python, hard)

Write a Python 3 module in a single file named `scheduler.py` that defines:

```python
def best_schedule(jobs: list[tuple[float, float, float]]) -> tuple[float, list[int]]:
    ...
```

`jobs` is a list of `(start, end, weight)` tuples. Choose a subset of jobs
such that no two chosen jobs overlap, maximizing the total weight. Two jobs
overlap when one starts strictly before the other ends — touching is allowed
(a job ending at time `t` is compatible with a job starting at `t`).

Return a tuple `(total_weight, chosen_indices)` where:

- `total_weight` is the maximum achievable sum of weights (float);
- `chosen_indices` are the indices **into the input list** of one optimal
  subset, sorted by the job's start time (break ties by index ascending).

## Rules

1. `start < end` for every job and `weight > 0`; you may assume valid input.
2. If `jobs` is empty, return `(0.0, [])`.
3. Any optimal subset is accepted — only the total weight must be the unique
   optimum; the index list just has to be a valid, non-overlapping subset
   achieving it.
4. **Performance is part of the spec.** The grader includes inputs with
   n = 200,000 jobs. Your solution must run in O(n log n) time. Brute force
   or O(n²) dynamic programming will time out (hard limit: 10 seconds for
   the large case on ordinary hardware; an O(n log n) solution takes well
   under 1 second).
5. Recursion-based solutions must not hit Python's recursion limit at
   n = 200,000 — use iteration.
6. Standard library only.

## Example

```python
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
best_schedule(jobs)  # -> (13.0, [2, 6])
# job 2 spans 0-6 (weight 8) and job 6 spans 6-11 (weight 5); they touch at
# t=6, which is allowed, for a total of 13. No other subset beats 13.
```

(The grader independently verifies both the claimed weight and the validity
of the chosen subset, on this example and on many hidden cases.)

## Constraints

- The file must be importable as `from scheduler import best_schedule` with
  no side effects on import.

**Deliverable: exactly one file, `scheduler.py`.**
