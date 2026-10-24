package main

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errors.New("pool: workers must be >= 1")
	}
	n := len(tasks)
	if n == 0 {
		return []any{}, nil
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, n)

	var (
		mu       sync.Mutex
		firstErr error
	)
	// fail records the first error and then cancels the task context.
	// The error is recorded before cancel so that errors caused by the
	// cancellation itself can never displace it.
	fail := func(err error) {
		mu.Lock()
		if firstErr == nil {
			if perr := ctx.Err(); perr != nil {
				// Parent was cancelled before we observed this error;
				// report the cancellation cause.
				firstErr = perr
			} else {
				firstErr = err
			}
		}
		mu.Unlock()
		cancel()
	}

	var next atomic.Int64
	var completed atomic.Int64

	numWorkers := workers
	if numWorkers > n {
		numWorkers = n
	}

	var wg sync.WaitGroup
	wg.Add(numWorkers)
	for w := 0; w < numWorkers; w++ {
		go func() {
			defer wg.Done()
			for {
				if runCtx.Err() != nil {
					return
				}
				idx := int(next.Add(1) - 1)
				if idx >= n {
					return
				}
				// Re-check right before starting so that nothing starts
				// after a failure/cancellation has been observed.
				if runCtx.Err() != nil {
					return
				}
				res, err := tasks[idx](runCtx)
				if err != nil {
					fail(err)
					return
				}
				results[idx] = res
				completed.Add(1)
			}
		}()
	}
	wg.Wait()

	mu.Lock()
	err := firstErr
	mu.Unlock()
	if err != nil {
		return nil, err
	}
	if int(completed.Load()) < n {
		// Some tasks never ran: the parent context must have been cancelled.
		if perr := ctx.Err(); perr != nil {
			return nil, perr
		}
		return nil, context.Canceled
	}
	return results, nil
}
