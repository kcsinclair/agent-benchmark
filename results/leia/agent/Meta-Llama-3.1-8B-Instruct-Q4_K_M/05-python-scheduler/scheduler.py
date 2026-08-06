import heapq

def best_schedule(jobs):
    # Sort jobs by end time
    jobs.sort(key=lambda x: x[1])

    # Initialize priority queue with first job
    pq = [(weight, [i]) for i, (start, end, weight) in enumerate(jobs) if start == end]
    heapq.heapify(pq)

    # Initialize result
    total_weight = 0
    chosen_indices = []

    # Iterate over remaining jobs
    for i, (start, end, weight) in enumerate(jobs):
        # If current job does not overlap with last chosen job, add it to priority queue
        if start >= end:  # This is a no-op, but ensures we don't add jobs that don't meet the problem's constraints
            continue
        if not pq or start >= pq[0][0]:  # If current job starts after the last chosen job, add it to the priority queue
            heapq.heappush(pq, (weight, [i]))
        else:  # Otherwise, try to add the current job to an existing subset
            while pq and start < pq[0][0]:  # While the current job overlaps with the last chosen job
                # Remove the last chosen job from the priority queue
                last_weight, last_indices = heapq.heappop(pq)
                # Add the current job to the last chosen job's subset
                last_indices.append(i)
                # Add the updated subset back to the priority queue
                heapq.heappush(pq, (last_weight + weight, last_indices))
                # If the current job does not overlap with the next chosen job, break the loop
                if not pq or start >= pq[0][0]:
                    break

    # If there are still jobs in the priority queue, choose the one with the highest weight
    if pq:
        total_weight, chosen_indices = max(pq)

    return total_weight, chosen_indices
