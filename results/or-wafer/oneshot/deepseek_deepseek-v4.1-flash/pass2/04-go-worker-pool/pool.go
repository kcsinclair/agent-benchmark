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

	n := len(tasks)
	results := make([]any, n)

	taskCtx, cancelTask := context.WithCancel(ctx)
	defer cancelTask()

	type outcome struct {
		err error
	}

	work := make(chan int)
	outcomes := make(chan outcome, n)

	var wg sync.WaitGroup
	wg.Add(workers)
	for w := 0; w < workers; w++ {
		go func() {
			defer wg.Done()
			for idx := range work {
				v, err := tasks[idx](taskCtx)
				if err == nil {
					results[idx] = v
				}
				outcomes <- outcome{err: err}
			}
		}()
	}

	dispatcherDone := make(chan struct{})
	go func() {
		defer close(dispatcherDone)
		defer close(work)
		for i := 0; i < n; i++ {
			select {
			case <-taskCtx.Done():
				return
			case work <- i:
			}
		}
	}()

	go func() {
		<-dispatcherDone
		wg.Wait()
		close(outcomes)
	}()

	var firstErr error
	for o := range outcomes {
		if o.err != nil && firstErr == nil {
			firstErr = o.err
			cancelTask()
		}
	}

	if firstErr != nil {
		return nil, firstErr
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}
	return results, nil
}
