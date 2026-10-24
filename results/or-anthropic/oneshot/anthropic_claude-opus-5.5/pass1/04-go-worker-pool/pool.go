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
		return nil, errors.New("pool: workers must be >= 1")
	}
	if ctx == nil {
		ctx = context.Background()
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	// Never allocate more semaphore slots than there are tasks.
	if workers > len(tasks) {
		workers = len(tasks)
	}

	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	var (
		mu       sync.Mutex
		firstErr error
		wg       sync.WaitGroup
	)
	results := make([]any, len(tasks))
	sem := make(chan struct{}, workers)

	// fail records the first error and cancels the task context.
	fail := func(err error) {
		mu.Lock()
		if firstErr == nil {
			if perr := ctx.Err(); perr != nil {
				// Parent was cancelled; report that, not a derived task error.
				firstErr = perr
			} else {
				firstErr = err
			}
		}
		cancel()
		mu.Unlock()
	}

dispatch:
	for i, t := range tasks {
		// Acquire a worker slot, or stop if cancelled.
		select {
		case <-taskCtx.Done():
			break dispatch
		case sem <- struct{}{}:
		}

		// Decide under the lock whether this task may start. Because fail()
		// cancels while holding mu, no task can start after the first error
		// has been recorded.
		mu.Lock()
		if firstErr != nil || taskCtx.Err() != nil {
			mu.Unlock()
			<-sem
			break dispatch
		}
		wg.Add(1)
		mu.Unlock()

		go func(i int, t Task) {
			defer wg.Done()
			defer func() { <-sem }()
			v, err := t(taskCtx)
			if err != nil {
				fail(err)
				return
			}
			results[i] = v
		}(i, t)
	}

	wg.Wait()

	mu.Lock()
	err := firstErr
	mu.Unlock()
	if err != nil {
		return nil, err
	}
	if perr := ctx.Err(); perr != nil {
		return nil, perr
	}
	return results, nil
}
