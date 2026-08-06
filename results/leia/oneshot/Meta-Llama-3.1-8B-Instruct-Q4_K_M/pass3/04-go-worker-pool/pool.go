package main

import (
	"context"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// runTask executes a single task and returns its result.
func runTask(ctx context.Context, task Task) (any, error) {
	return task(ctx)
}

// runTaskWithCancel executes a single task and returns its result.
// If the task context is cancelled, it will be cancelled as well.
func runTaskWithCancel(ctx context.Context, task Task) (any, error) {
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()
	return runTask(ctx, task)
}

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, errors.New("workers must be at least 1")
	}

	if len(tasks) == 0 {
		return []any{}, nil
	}

	var (
		results = make([]any, len(tasks))
		errs    = make(chan error, len(tasks))
		wg      = &sync.WaitGroup{}
	)

	for i := range tasks {
		wg.Add(1)
		go func(i int) {
			defer wg.Done()
			results[i], errs <- runTaskWithCancel(ctx, tasks[i])
		}(i)
	}

	go func() {
		for i := range tasks {
			select {
			case err := <-errs:
				close(errs)
				wg.Wait()
				return
			case <-ctx.Done():
				close(errs)
				wg.Wait()
				return
			}
		}
	}()

	go func() {
		for i := range tasks {
			select {
			case err := <-errs:
				close(errs)
				wg.Wait()
				return
			case <-ctx.Done():
				close(errs)
				wg.Wait()
				return
			default:
				wg.Add(1)
				go func(i int) {
					defer wg.Done()
					results[i], errs <- runTaskWithCancel(ctx, tasks[i])
				}(i)
			}
		}
	}()

	wg.Wait()

	close(errs)

	for err := range errs {
		if err != nil {
			return nil, err
		}
	}

	return results, nil
}
