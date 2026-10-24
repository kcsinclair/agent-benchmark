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
			cancel()
		}
		mu.Unlock()
	}

	// Feeder sends indices to workers; stops early on cancellation.
	idxCh := make(chan int)
	go func() {
		defer close(idxCh)
		for i := range tasks {
			select {
			case idxCh <- i:
			case <-runCtx.Done():
				return
			}
		}
	}()

	var wg sync.WaitGroup
	for w := 0; w < workers; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for i := range idxCh {
				// Don't start a task if already cancelled.
				if runCtx.Err() != nil {
					return
				}
				v, err := tasks[i](runCtx)
				if err != nil {
					setErr(fmt.Errorf("task %d: %w", i, err))
					return
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
	if cerr := ctx.Err(); cerr != nil {
		return nil, cerr
	}
	return results, nil
}
