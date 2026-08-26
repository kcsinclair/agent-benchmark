package main

import (
    "context"
    "errors"
    "sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(parent context.Context, tasks []Task, workers int) ([]any, error) {
    // Validation.
    if workers < 1 {
        return nil, errors.New("workers must be >= 1")
    }
    if len(tasks) == 0 {
        // Empty slice is acceptable.
        return nil, nil
    }

    // Context that can be cancelled on first error or parent cancellation.
    ctx, cancel := context.WithCancel(parent)
    defer cancel()

    // Semaphore to bound concurrency.
    sem := make(chan struct{}, workers)

    results := make([]any, len(tasks))
    var wg sync.WaitGroup
    var once sync.Once
    var firstErr error

    // Record the first error and cancel the derived context.
    setErr := func(err error) {
        once.Do(func() {
            firstErr = err
            cancel()
        })
    }

    // Launch tasks respecting the concurrency limit and early cancellation.
    // Use a labeled loop so we can break from inside select.
    launchLoop:
    for i, task := range tasks {
        // Before trying to acquire a slot, check if we have already been cancelled.
        select {
        case <-ctx.Done():
            // Context cancelled (error or parent cancellation); stop launching.
            break launchLoop
        case sem <- struct{}{}:
            // Acquired a slot, proceed.
        }

        // After acquiring a slot, it's possible the context was cancelled in the
        // tiny window before we started the goroutine. If so, release the slot and stop.
        if ctx.Err() != nil {
            // Release the token we just took.
            <-sem
            break launchLoop
        }

        wg.Add(1)
        go func(idx int, t Task) {
            defer wg.Done()
            // Ensure the semaphore token is released when the task finishes.
            defer func() { <-sem }()

            res, err := t(ctx)
            if err != nil {
                setErr(err)
                return
            }
            results[idx] = res
        }(i, task)
    }

    // Wait for any started tasks to finish.
    wg.Wait()

    // Determine the appropriate return value.
    if firstErr != nil {
        return nil, firstErr
    }
    if ctx.Err() != nil {
        // No task error, but the context was cancelled (e.g., parent timeout).
        return nil, ctx.Err()
    }
    return results, nil
}
