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
                j = len(chosen_indices) - 1 - chosen_indices.index(min((jobs[j][1], -x[0])))
                if start >= jobs[j][1]:
                    # If the current job can replace the last chosen one, replace it
                    total_weight -= sum((w for _, w, _) in zip((jobs[k][2] for k in range(j + 1)), (total_weight - sum((w for _, w, _) in zip((jobs[k][2] for k in range(j + 1)), range(j + 1)))))))
                    chosen_indices = chosen_indices[:j + 1]
                    current_end = jobs[j][1]
                    break
            if start >= current_end:
                # If no better schedule can be found, skip this job
                continue
            # Otherwise, add the current job to the current schedule
            total_weight += weight
            chosen_indices.append(i)
            current_end = end

    return (total_weight, chosen_indices)
