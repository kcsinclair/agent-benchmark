package main

import (
    "context"
    "fmt"
    "sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
    if workers < 1 {
        return nil, fmt.Errorf("workers must be >= 1")
    }
    if len(tasks) == 0 {
        return []any{}, nil
    }

    // Preserve the original context to detect parent cancellation.
    parentCtx := ctx
    // Create a cancellable context for the workers.
    ctx, cancel := context.WithCancel(parentCtx)
    defer cancel()

    results := make([]any, len(tasks))
    // Channel to capture the first error from any task.
    errCh := make(chan error, 1)
    // Semaphore to limit concurrency.
    sem := make(chan struct{}, workers)

    var wg sync.WaitGroup

outer:
    for i, t := range tasks {
        // Stop launching new tasks if either the parent or worker context is done.
        select {
        case <-parentCtx.Done():
            cancel()
            break outer
        case <-ctx.Done():
            // Already cancelled due to a task error.
            break outer
        default:
        }

        // Acquire semaphore slot.
        sem <- struct{}{}
        wg.Add(1)
        go func(idx int, task Task) {
            defer wg.Done()
            defer func() { <-sem }()
            res, err := task(ctx)
            if err != nil {
                // Send the first error and cancel the context.
                select {
                case errCh <- err:
                    cancel()
                default:
                }
                return
            }
            results[idx] = res
        }(i, t)
    }

    // Wait for all started goroutines to finish.
    wg.Wait()

    // If a task error occurred, return it.
    select {
    case err := <-errCh:
        return nil, err
    default:
    }

    // If the parent context was cancelled, return its error.
    if parentCtx.Err() != nil {
        return nil, parentCtx.Err()
    }

    return results, nil
}
