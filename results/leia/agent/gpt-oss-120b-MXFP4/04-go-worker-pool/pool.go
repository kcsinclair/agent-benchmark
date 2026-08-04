package main

import (
    "context"
    "errors"
    "fmt"
    "sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
    // Validation
    if workers < 1 {
        return nil, fmt.Errorf("workers must be >= 1, got %d", workers)
    }
    if len(tasks) == 0 {
        // Return nil slice (or empty) and nil error as per spec.
        return nil, nil
    }

    // Derive a cancellable context that we can cancel on first error or parent cancellation.
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()

    // Channel to feed tasks to workers.
    type job struct {
        idx  int
        task Task
    }
    jobCh := make(chan job)

    // Slice to store results; will be filled only on success.
    results := make([]any, len(tasks))

    var wg sync.WaitGroup
    var once sync.Once
    var firstErr error

    // Helper to record the first error and cancel the context.
    recordError := func(err error) {
        once.Do(func() {
            firstErr = err
            cancel()
        })
    }

    // Start worker goroutines.
    wg.Add(workers)
    for w := 0; w < workers; w++ {
        go func() {
            defer wg.Done()
            for {
                select {
                case <-ctx.Done():
                    // Context cancelled – stop processing new jobs.
                    return
                case j, ok := <-jobCh:
                    if !ok {
                        // No more jobs.
                        return
                    }
                    // Execute the task.
                    val, err := j.task(ctx)
                    if err != nil {
                        recordError(err)
                    }
                    // Store result regardless of error; on error we will discard slice later.
                    results[j.idx] = val
                }
            }
        }()
    }

    // Feed jobs respecting cancellation.
    feedDone := make(chan struct{})
    go func() {
        defer close(feedDone)
        for i, t := range tasks {
            select {
            case <-ctx.Done():
                // Stop feeding further tasks.
                return
            case jobCh <- job{idx: i, task: t}:
                // sent
            }
        }
    }()

    // Wait for feeding to finish, then close job channel.
    <-feedDone
    close(jobCh)

    // Wait for all workers to finish.
    wg.Wait()

    // Determine final outcome.
    if firstErr != nil {
        return nil, firstErr
    }
    if ctx.Err() != nil && !errors.Is(ctx.Err(), context.Canceled) && !errors.Is(ctx.Err(), context.DeadlineExceeded) {
        // Should not happen, but preserve semantics.
        return nil, ctx.Err()
    }
    if ctx.Err() != nil {
        // Context cancelled (by parent or due to error). Return appropriate error.
        // If it was cancelled because of an earlier task error, firstErr already set.
        // Otherwise, propagate context error.
        return nil, ctx.Err()
    }
    return results, nil
}
