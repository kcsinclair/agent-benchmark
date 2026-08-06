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
        return nil, fmt.Errorf("workers must be at least 1")
    }

    if len(tasks) == 0 {
        return []any{}, nil
    }

    results := make([]any, len(tasks))
    taskCh := make(chan Task, workers)
    resultCh := make(chan any, len(tasks))
    done := make(chan struct{}, workers)

    var wg sync.WaitGroup

    // Start workers.
    for i := 0; i < workers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for {
                select {
                case task, ok := <-taskCh:
                    if !ok {
                        return
                    }
                    result, err := executeTask(ctx, task)
                    if err != nil {
                        // Cancel task context if it has not been cancelled yet.
                        cancelTaskContext(ctx)
                        // Return the first error that occurred.
                        return nil, err
                    }
                    // Send the result to the result channel.
                    resultCh <- result
                case <-done:
                    return
                }
            }
        }()
    }

    // Execute tasks.
    for i, task := range tasks {
        taskCh <- task
        results[i] = <-resultCh
    }

    // Close task channel to stop workers.
    close(taskCh)

    // Wait for workers to finish.
    wg.Wait()

    // Close result channel to prevent further sends.
    close(resultCh)

    // Return results.
    return results, nil
}

// Helper function to execute a task and return its result.
func executeTask(ctx context.Context, task Task) (any, error) {
    return task(ctx)
}

// Helper function to cancel a task context.
func cancelTaskContext(ctx context.Context) {
    ctx.Done()
}

// Helper function to wait for a task to finish.
func waitForTask(ctx context.Context, task any) {
    // Wait for the task to finish.
}
