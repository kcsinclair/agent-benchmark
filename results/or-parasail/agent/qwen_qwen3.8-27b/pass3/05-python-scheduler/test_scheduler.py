import random
import time
from scheduler import best_schedule

# Example from the problem
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
print("example:", best_schedule(jobs))

# Empty
print("empty:", best_schedule([]))

# Single
print("single:", best_schedule([(0, 1, 2.5)]))

# Brute force cross-check
def brute(jobs):
    n = len(jobs)
    best = 0.0
    best_set = None
    for mask in range(1 << n):
        sel = [i for i in range(n) if mask >> i & 1]
        # check non-overlap
        ok = True
        sel_sorted = sorted(sel, key=lambda i: (jobs[i][0], jobs[i][1]))
        for a, b in zip(sel_sorted, sel_sorted[1:]):
            if jobs[a][1] > jobs[b][0]:
                ok = False
                break
        if not ok:
            continue
        w = sum(jobs[i][2] for i in sel)
        if w > best:
            best = w
            best_set = sel
    return best

random.seed(1)
for trial in range(300):
    n = random.randint(1, 10)
    jobs = []
    for _ in range(n):
        s = random.uniform(0, 20)
        e = s + random.uniform(0.1, 5)
        w = random.uniform(0.1, 10)
        jobs.append((s, e, w))
    got_w, got_idx = best_schedule(jobs)
    exp_w = brute(jobs)
    assert abs(got_w - exp_w) < 1e-9, (jobs, got_w, exp_w)
    # validate chosen subset
    sel = sorted(got_idx, key=lambda i: (jobs[i][0], jobs[i][1]))
    for a, b in zip(sel, sel[1:]):
        assert jobs[a][1] <= jobs[b][0], (jobs, got_idx)
    assert abs(sum(jobs[i][2] for i in got_idx) - got_w) < 1e-9
print("random cross-check OK")

# Performance test
n = 200000
random.seed(2)
jobs = []
for _ in range(n):
    s = random.uniform(0, 1e6)
    e = s + random.uniform(0.1, 100)
    w = random.uniform(0.1, 100)
    jobs.append((s, e, w))
t0 = time.time()
w, idx = best_schedule(jobs)
t1 = time.time()
print(f"n={n}: weight={w}, chosen={len(idx)}, time={t1-t0:.3f}s")
