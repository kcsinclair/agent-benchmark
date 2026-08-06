import heapq

def best_schedule(jobs):
    if not jobs:
        return (0.0, [])

    # Sort jobs by end time and then by weight in descending order
    jobs.sort(key=lambda x: (-x[1], -x[0]))

    # Initialize variables
    total_weight = 0.0
    chosen_indices = []
    current_end = float('inf')

    # Greedy schedule jobs greedily
    for i, (start, end, weight) in enumerate(jobs):
        if start >= current_end:
            # If the current job does not conflict with the previous one, add it
            total_weight += weight
            chosen_indices.append(i)
            current_end = end
        else:
            # Otherwise, try to insert the current job into the current schedule
            while chosen_indices and start < current_end:
                j = chosen_indices.index(min((j, j - start) for j, _ in enumerate(jobs) if j != i)[0])
                if end <= jobs[j][1]:
                    # If the current job can be inserted before the last chosen job, insert it
                    total_weight -= sum((w for w, _, _) in [(w, _[1], _[2]) for _, w, _ in zip((w for w, _, _ in jobs if w > 0), heapq[-len(jobs):][::-1]) if w > 0][::-1]))
                    chosen_indices = chosen_indices[:j]
                    break
                else:
                    # Otherwise, remove the last chosen job and try again
                    total_weight -= sum((w for w, _, _ in [(w, _[1], _[2]) for _, w, _ in zip((w for w, _, _ in reversed(list(zip(*sorted((w, start, end) for start, end, w) if w > 0), key=lambda x: -x[1]))[::-1])) if w > 0]))[::-1])
                    current_end = end
                    break
            if not chosen_indices:
                return (0.0, [])

    return (total_weight, chosen_indices[::-1])
