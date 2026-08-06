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
            while chosen_indices and start < jobs[chosen_indices[-1]][1]:
                # Find the last chosen job that does not conflict with the current one
                j = len(chosen_indices) - 1
                while j > 0 and start >= jobs[chosen_indices[j-1]][1]:
                    j -= 1
                if j == len(chosen_indices):
                    # If no such job is found, break the loop
                    break
                # Update the total weight and the current end of the current schedule
                total_weight -= sum((w for _, _, w in jobs[i+1:])) + sum((w for _, _, w in zip((w for _, _, w in jobs[:j+1][::-1]))[1:][::-1], range(len(chosen_indices) - j - 1, -1, -1))))
                current_end = jobs[chosen_indices.pop()][1]
                total_weight += sum((w for _, _, w in zip((w for _, _, w in jobs[:j+1][::-1]))[1:][::-1], range(len(chosen_indices) + 1, -1, -1)))[::-1]
                break

    return (total_weight, chosen_indices[::-1])
