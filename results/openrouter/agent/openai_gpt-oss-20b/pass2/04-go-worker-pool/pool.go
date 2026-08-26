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
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
    // Validation
    if workers < 1 {
        return nil, errors.New("workers must be >= 1")
    }
    if len(tasks) == 0 {
        return []any{}, nil
    }

    // Context that can be cancelled on error or parent cancellation.
    ctx2, cancel := context.WithCancel(ctx)
    defer cancel()

    results := make([]any, len(tasks))

    // Channels for task indices and error handling.
    idxCh := make(chan int, workers)
    errCh := make(chan error, 1) // buffer 1 to capture first error
    errorSignal := make(chan struct{}, 1) // signal that an error occurred

    var wg sync.WaitGroup
    var once sync.Once

    // Goroutine to capture parent context cancellation.
    go func() {
        <-ctx2.Done()
        once.Do(func() {
            errCh <- ctx2.Err()
        })
    }()

    // Start worker goroutines.
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for idx := range idxCh {
                // Check if context is cancelled before starting a task.
                select {
                case <-ctx2.Done():
                    return
                default:
                }
                res, err := tasks[idx](ctx2)
                if err != nil {
                    // Capture the first error.
                    once.Do(func() {
                        errCh <- err
                    })
                    // Signal that an error occurred.
                    select {
                    case errorSignal <- struct{}{}:
                    default:
                    }
                    cancel()
                    return
                }
                results[idx] = res
            }
        }()
    }

    // Dispatch tasks.
dispatchLoop:
    for i := range tasks {
        select {
        case <-ctx2.Done():
            break dispatchLoop
        case <-errorSignal:
            break dispatchLoop
        case idxCh <- i:
            // dispatched
        }
    }
    close(idxCh)

    // Wait for all workers to finish.
    wg.Wait()

    // Return the first error if any.
    select {
    case err := <-errCh:
        return nil, err
    default:
        return results, nil
    }
}
