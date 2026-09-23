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
	if len(tasks) == 0 {
		return []any{}, nil
	}

	taskCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	// done is closed once every started task has finished, so that Run can
	// return the first error without spawning extra goroutines or leaking.
	var done sync.WaitGroup

	// firstErr records the earliest error observed. Protected by mu.
	var (
		mu         sync.Mutex
		firstErr   error
		haveErr    bool
		cancelOnce sync.Once
	)

	recordErr := func(err error) {
		if err == nil {
			return
		}
		mu.Lock()
		if !haveErr {
			haveErr = true
			firstErr = err
		}
		mu.Unlock()
	}

	failCtx := func() {
		mu.Lock()
		needCancel := haveErr
		mu.Unlock()
		if needCancel {
			// Only the first observed failure triggers, but cancelling
			// repeatedly is harmless; Once keeps it clean.
			cancelOnce.Do(cancel)
		}
	}

	// A single dispatcher goroutine feeds indices to a channel. It stops as
	// soon as the task context is cancelled (parent cancellation or the
	// first task error), guaranteeing tasks not yet started never start.
	indexCh := make(chan int)

	go func() {
		defer close(indexCh)
		for i := range tasks {
			select {
			case <-taskCtx.Done():
				return
			case indexCh <- i:
			}
		}
	}()

	var wg sync.WaitGroup
	wg.Add(workers)
	for w := 0; w < workers; w++ {
		go func() {
			defer wg.Done()
			for i := range indexCh {
				v, err := tasks[i](taskCtx)
				if err != nil {
					recordErr(err)
					failCtx()
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
	if ctxErr := ctx.Err(); ctxErr != nil {
		return nil, ctxErr
	}
	return results, nil
}
