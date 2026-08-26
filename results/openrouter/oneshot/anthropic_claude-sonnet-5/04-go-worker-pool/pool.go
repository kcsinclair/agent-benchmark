// pool.go
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
	if workers < 1 {
		return nil, fmt.Errorf("pool: workers must be >= 1, got %d", workers)
	}
	if len(tasks) == 0 {
		return nil, nil
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	var errOnce sync.Once
	var firstErr error

	indices := make(chan int)

	var wg sync.WaitGroup

	// Feeder goroutine: sends task indices to workers, respecting
	// cancellation so no new tasks start after failure/cancellation.
	go func() {
		defer close(indices)
		for i := range tasks {
			select {
			case <-runCtx.Done():
				return
			case indices <- i:
			}
		}
	}()

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range indices {
				// Double-check cancellation before actually starting the task,
				// to avoid starting new tasks after a failure occurred.
				select {
				case <-runCtx.Done():
					return
				default:
				}

				res, err := tasks[i](runCtx)
				if err != nil {
					errOnce.Do(func() {
						firstErr = err
						cancel()
					})
					continue
				}
				results[i] = res
			}
		}()
	}

	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}

	if err := ctx.Err(); err != nil {
		return nil, err
	}

	if err := runCtx.Err(); err != nil {
		// runCtx was cancelled but not due to a task error or parent ctx;
		// shouldn't normally happen, but guard anyway.
		if errors.Is(err, context.Canceled) && ctx.Err() == nil && firstErr == nil {
			// This means our own cancel() was called due to firstErr being set,
			// but firstErr is nil here — shouldn't occur given logic above.
			// Fall through safely.
		}
	}

	return results, nil
}
