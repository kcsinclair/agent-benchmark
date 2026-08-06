// pool.go
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
		return nil, errors.New("workers must be at least 1")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Result slice
	results := make([]any, len(tasks))

	// Channel for task indices
	taskCh := make(chan int)

	// Channel for the first error (buffered to avoid blocking)
	errCh := make(chan error, 1)

	// Context that can be cancelled on error or parent cancellation
	ctx2, cancel := context.WithCancel(ctx)
	defer cancel()

	// WaitGroup for workers
	var wg sync.WaitGroup
	wg.Add(workers)

	// Worker goroutine
	worker := func() {
		defer wg.Done()
		for idx := range taskCh {
			res, err := tasks[idx](ctx2)
			if err != nil {
				// Record the first error
				select {
				case errCh <- err:
				default:
				}
				// Cancel the context to stop other tasks
				cancel()
				continue
			}
			results[idx] = res
		}
	}

	// Start workers
	for i := 0; i < workers; i++ {
		go worker()
	}

	// Feed task indices to workers
	go func() {
		defer close(taskCh)
		for idx := 0; idx < len(tasks); idx++ {
			select {
			case <-ctx2.Done():
				return
			case taskCh <- idx:
			}
		}
	}()

	// Wait for all workers to finish
	wg.Wait()

	// Determine the error to return
	var firstErr error
	select {
	case firstErr = <-errCh:
	default:
	}

	if firstErr != nil {
		return nil, firstErr
	}
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	return results, nil
}
