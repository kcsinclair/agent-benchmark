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
	if workers < 1 {
		return nil, errors.New("workers must be at least 1")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Derived context that gets cancelled on first error or parent cancellation.
	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	var firstErr error
	var errOnce sync.Once
	var wg sync.WaitGroup

	// Channel to distribute task indices to workers.
	taskIdx := make(chan int, len(tasks))
	for i := range tasks {
		taskIdx <- i
	}
	close(taskIdx)

	// Launch exactly `workers` goroutines; each pulls indices until the
	// channel is drained or the context is cancelled.
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for idx := range taskIdx {
				// If the context is already cancelled (due to a prior error
				// or parent cancellation), stop pulling new tasks.
				if taskCtx.Err() != nil {
					return
				}

				result, err := tasks[idx](taskCtx)
				if err != nil {
					errOnce.Do(func() {
						firstErr = err
						cancel() // signal all other workers to stop
					})
				} else {
					results[idx] = result
				}
			}
		}()
	}

	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	return results, nil
}
