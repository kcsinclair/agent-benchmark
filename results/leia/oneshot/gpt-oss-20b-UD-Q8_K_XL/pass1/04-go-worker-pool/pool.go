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
	// Validation
	if workers < 1 {
		return nil, fmt.Errorf("workers must be >= 1")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}

	// Child context that we can cancel when an error occurs or the parent
	// context is cancelled.
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	// A buffered channel that limits the number of concurrently running tasks.
	tokens := make(chan struct{}, workers)
	// Channel used to report the first error that occurs.
	errorCh := make(chan error, 1)

	var wg sync.WaitGroup
	var firstErr error

	for idx, t := range tasks {
		// Check for cancellation or a previously reported error before
		// acquiring a token.
		select {
		case <-ctx.Done():
			firstErr = ctx.Err()
			cancel()
			goto done
		case err := <-errorCh:
			firstErr = err
			cancel()
			goto done
		default:
		}

		// Acquire a token to respect the worker limit.
		select {
		case <-ctx.Done():
			firstErr = ctx.Err()
			cancel()
			goto done
		case err := <-errorCh:
			firstErr = err
			cancel()
			goto done
		case tokens <- struct{}{}:
			// token acquired
		}

		wg.Add(1)
		go func(i int, task Task) {
			defer wg.Done()
			defer func() { <-tokens }() // release token

			res, err := task(ctx)
			if err != nil {
				// Send the first error only.
				select {
				case errorCh <- err:
				default:
				}
				return
			}
			results[i] = res
		}(idx, t)
	}

done:
	// Wait for all started tasks to finish.
	wg.Wait()

	// Return the first error that occurred, if any.
	if firstErr != nil {
		return nil, firstErr
	}
	// If the context was cancelled after all tasks finished.
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	return results, nil
}
