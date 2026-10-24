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
		return nil, errors.New("pool: workers must be >= 1")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}
	if ctx == nil {
		ctx = context.Background()
	}

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
		}
		mu.Unlock()
		cancel()
	}

	// Feed indices to workers through a channel; the producer stops when
	// the run context is cancelled, so unstarted tasks never begin.
	indices := make(chan int)
	var wg sync.WaitGroup

	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range indices {
				// Re-check cancellation before starting a task.
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
	if perr := ctx.Err(); perr != nil {
		return nil, fmt.Errorf("pool: %w", perr)
	}
	return results, nil
}
