import time
import random
from scheduler import best_schedule

# Large test: n = 200,000 with random jobs
random.seed(0)
n = 200000
jobs = []
for i in range(n):
    s = random.random() * 1000
    e = s + 1 + random.random() * 100  # ensure e > s
    w = 1 + random.random() * 1000
    jobs.append((s, e, w))

start = time.time()
weight, idx = best_schedule(jobs)
elapsed = time.time() - start
print(f"n={n}, weight={weight:.2f}, indices_count={len(idx)}, time={elapsed:.3f}s")

# Validate result - check non-overlapping
chosen = [(jobs[i][0], jobs[i][1], i) for i in idx]
conflict = False
for a in range(len(chosen)):
    for b in range(a + 1, len(chosen)):
        s1, e1, idx1 = chosen[a]
        s2, e2, idx2 = chosen[b]
        if s1 < e2 and s2 < e1:  # overlap
            print(f"CONFLICT between {chosen[a]} and {chosen[b]}")
            conflict = True
            break
    if conflict:
        break
if not conflict:
    print("No conflicts found in large test.")

# Check total weight is reasonable
max_single = max(job[2] for job in jobs)
assert weight >= max_single - 1e-6, f"Weight {weight} less than max single {max_single}"
print(f"Large test passed. Weight {weight} >= max single {max_single}, time={elapsed:.3f}s")
