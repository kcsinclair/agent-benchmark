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
		return []any{}, nil
	}
	if ctx == nil {
		ctx = context.Background()
	}

	// Derived context: cancelled on first task error or when parent is cancelled.
	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	var (
		mu       sync.Mutex
		firstErr error
	)
	setErr := func(err error) {
		mu.Lock()
		if firstErr == nil {
			firstErr = err
			cancel()
		}
		mu.Unlock()
	}

	// Feeder sends indices to workers; stops early on cancellation so that
	// unstarted tasks never begin.
	indices := make(chan int)
	var wg sync.WaitGroup

	n := workers
	if n > len(tasks) {
		n = len(tasks)
	}

	for w := 0; w < n; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range indices {
				// Re-check cancellation before starting the task.
				if runCtx.Err() != nil {
					continue
				}
				v, err := tasks[i](runCtx)
				if err != nil {
					setErr(err)
					continue
				}
				results[i] = v
			}
		}()
	}

feed:
	for i := range tasks {
		select {
		case <-runCtx.Done():
			break feed
		case indices <- i:
		}
	}
	close(indices)
	wg.Wait()

	mu.Lock()
	err := firstErr
	mu.Unlock()

	if err != nil {
		return nil, err
	}
	if cerr := ctx.Err(); cerr != nil {
		return nil, cerr
	}
	return results, nil
}

// ensure errors import is used even if no sentinel errors are declared.
var _ = errors.New
