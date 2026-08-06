package main

import (
	"context"
	"fmt"
	"sync"
)

// Task is one unit of work.
type Task func(ctx context.Context) (any, error)

// Run executes tasks with at most `workers` running concurrently and returns
// their results in the same order as the input slice.
func Run(ctx context.Context, tasks []Task, workers int) ([]any, error) {
	if workers < 1 {
		return nil, fmt.Errorf("workers must be >= 1")
	}
	if len(tasks) == 0 {
		return nil, nil
	}

	// Derived context that can be cancelled when an error occurs or the parent
	// context is cancelled.
	ctx2, cancel := context.WithCancel(ctx)
	defer cancel()

	results := make([]any, len(tasks))
	sem := make(chan struct{}, workers) // semaphore to limit concurrency

	var wg sync.WaitGroup
	var once sync.Once
	var firstErr error

outer:
	for i, t := range tasks {
		// Stop starting new tasks if the context is already cancelled.
		select {
		case <-ctx2.Done():
			break outer
		case sem <- struct{}{}:
			// acquired a slot
		}

		wg.Add(1)
		go func(i int, t Task) {
			defer wg.Done()
			defer func() { <-sem }() // release the slot

			res, err := t(ctx2)
			if err != nil {
				once.Do(func() {
					firstErr = err
					cancel() // cancel the context to stop other tasks
				})
			}
			results[i] = res
		}(i, t)
	}

	// Wait for all started tasks to finish.
	wg.Wait()

	if firstErr != nil {
		return nil, firstErr
	}
	if ctx2.Err() != nil {
		return nil, ctx2.Err()
	}
	return results, nil
}
