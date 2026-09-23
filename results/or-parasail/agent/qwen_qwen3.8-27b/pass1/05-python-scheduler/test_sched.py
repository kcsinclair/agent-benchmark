import random
import time
from scheduler import best_schedule

# Example
jobs = [(1, 4, 5), (3, 5, 1), (0, 6, 8), (4, 7, 4), (3, 9, 6), (5, 10, 3), (6, 11, 5)]
print(best_schedule(jobs))

# Empty
print(best_schedule([]))

# Brute force check on small random cases
def brute(jobs):
    n = len(jobs)
    best = 0.0
    for mask in range(1 << n):
        sel = [i for i in range(n) if mask >> i & 1]
        ok = True
        sel.sort(key=lambda i: (jobs[i][0], jobs[i][1]))
        for a, b in zip(sel, sel[1:]):
            if jobs[a][1] > jobs[b][0]:
                ok = False
                break
        if ok:
            w = sum(jobs[i][2] for i in sel)
            if w > best:
                best = w
    return best

random.seed(1)
for t in range(300):
    n = random.randint(1, 10)
    jobs = []
    for _ in range(n):
        s = random.uniform(0, 20)
        e = s + random.uniform(0.1, 10)
        w = random.uniform(0.1, 100)
        jobs.append((s, e, w))
    got, idx = best_schedule(jobs)
    exp = brute(jobs)
    assert abs(got - exp) < 1e-9, (jobs, got, exp)
    # validate idx
    sel = sorted(idx, key=lambda i: (jobs[i][0], jobs[i][1]))
    for a, b in zip(sel, sel[1:]):
        assert jobs[a][1] <= jobs[b][0], (jobs, idx)
    assert abs(sum(jobs[i][2] for i in idx) - got) < 1e-9
print("small random OK")

# Performance test
n = 200000
random.seed(2)
jobs = []
for _ in range(n):
    s = random.uniform(0, 1e6)
    e = s + random.uniform(0.1, 1000)
    w = random.uniform(0.1, 1000)
    jobs.append((s, e, w))
t0 = time.time()
res = best_schedule(jobs)
t1 = time.time()
print("n=200000 time:", t1 - t0, "weight:", res[0], "chosen:", len(res[1]))
