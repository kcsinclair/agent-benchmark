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
		return nil, errors.New("workers must be at least 1")
	}
	if len(tasks) == 0 {
		return []any{}, nil
	}
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	childCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))

	var firstErr error
	var once sync.Once
	setErr := func(err error) {
		if err != nil {
			once.Do(func() {
				firstErr = err
				cancel()
			})
		}
	}

	numWorkers := workers
	if numWorkers > len(tasks) {
		numWorkers = len(tasks)
	}

	type taskItem struct {
		index int
		task  Task
	}

	taskCh := make(chan taskItem)
	var wg sync.WaitGroup
	wg.Add(numWorkers)

	for w := 0; w < numWorkers; w++ {
		go func() {
			defer wg.Done()
			for item := range taskCh {
				if childCtx.Err() != nil {
					continue
				}
				res, err := item.task(childCtx)
				if err != nil {
					setErr(err)
				} else {
					results[item.index] = res
				}
			}
		}()
	}

feedLoop:
	for i, t := range tasks {
		select {
		case <-childCtx.Done():
			setErr(childCtx.Err())
			break feedLoop
		case taskCh <- taskItem{index: i, task: t}:
		}
	}
	close(taskCh)
	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}
	return results, nil
}
