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
		return nil, nil
	}

	runCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	var errOnce sync.Once
	var firstErr error

	setErr := func(err error) {
		errOnce.Do(func() {
			firstErr = err
			cancel()
		})
	}

	indices := make(chan int)

	var feedWG sync.WaitGroup
	feedWG.Add(1)
	go func() {
		defer feedWG.Done()
		defer close(indices)
		for i := range tasks {
			select {
			case <-runCtx.Done():
				return
			case indices <- i:
			}
		}
	}()

	var workerWG sync.WaitGroup
	for w := 0; w < workers; w++ {
		workerWG.Add(1)
		go func() {
			defer workerWG.Done()
			for i := range indices {
				res, err := tasks[i](runCtx)
				if err != nil {
					setErr(err)
					continue
				}
				results[i] = res
			}
		}()
	}

	workerWG.Wait()
	feedWG.Wait()

	if firstErr != nil {
		return nil, firstErr
	}

	if ctx.Err() != nil {
		return nil, ctx.Err()
	}

	return results, nil
}
