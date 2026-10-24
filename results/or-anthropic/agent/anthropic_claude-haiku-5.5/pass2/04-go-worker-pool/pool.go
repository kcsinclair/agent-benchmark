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

	taskCtx, cancel := context.WithCancel(ctx)
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

	// Feeder: sends indices until done or cancelled. Unbuffered so that
	// no task starts after cancellation is observed by the select.
	indices := make(chan int)
	go func() {
		defer close(indices)
		for i := range tasks {
			select {
			case indices <- i:
			case <-taskCtx.Done():
				return
			}
		}
	}()

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
				if taskCtx.Err() != nil {
					return
				}
				v, err := tasks[i](taskCtx)
				if err != nil {
					setErr(fmt.Errorf("task %d: %w", i, err))
					continue
				}
				results[i] = v
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
	if ctx.Err() != nil {
		return nil, ctx.Err()
	}
	return results, nil
}
