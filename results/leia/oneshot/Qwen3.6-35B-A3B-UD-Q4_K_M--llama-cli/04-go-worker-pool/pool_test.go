package main

import (
	"context"
	"errors"
	"fmt"
	"sync/atomic"
	"testing"
	"time"
)

func TestRun_SingleWorker(t *testing.T) {
	tasks := []Task{
		func(ctx context.Context) (any, error) { return int64(1), nil },
		func(ctx context.Context) (any, error) { return int64(2), nil },
		func(ctx context.Context) (any, error) { return int64(3), nil },
	}
	results, err := Run(context.Background(), tasks, 1)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	for i, exp := range []any{int64(1), int64(2), int64(3)} {
		if results[i] != exp {
			t.Fatalf("results[%d] = %v, want %v", i, results[i], exp)
		}
	}
}

func TestRun_MultipleWorkers(t *testing.T) {
	var running atomic.Int64
	var maxRunning atomic.Int64
	tasks := make([]Task, 10)
	for i := range tasks {
		tasks[i] = func(ctx context.Context) (any, error) {
			n := running.Add(1)
			if n > maxRunning.Load() {
				maxRunning.Store(n)
			}
			defer running.Add(-1)
			time.Sleep(10 * time.Millisecond)
			return i, nil
		}
	}
	results, err := Run(context.Background(), tasks, 4)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if int64(len(results)) != 10 {
		t.Fatalf("len(results) = %d, want 10", len(results))
	}
	for i, res := range results {
		if res != i {
			t.Fatalf("results[%d] = %v, want %d", i, res, i)
		}
	}
	if maxRunning.Load() > 4 {
		t.Fatalf("max concurrent = %d, want <= 4", maxRunning.Load())
	}
}

func TestRun_Validation(t *testing.T) {
	_, err := Run(context.Background(), nil, 0)
	if err == nil {
		t.Fatal("expected error for workers=0")
	}
	if err == nil {
		t.Fatal("expected error for workers=-1")
	}
	_, err = Run(context.Background(), nil, -1)
	if err == nil {
		t.Fatal("expected error for workers=-1")
	}
}

func TestRun_EmptyTasks(t *testing.T) {
	results, err := Run(context.Background(), []Task{}, 5)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 0 {
		t.Fatalf("len(results) = %d, want 0", len(results))
	}
}

func TestRun_FailFast(t *testing.T) {
	// Use workers=1 to ensure strict sequential execution for fail-fast test
	var started atomic.Int64
	tasks := make([]Task, 5)
	for i := range tasks {
		tasks[i] = func(ctx context.Context) (any, error) {
			started.Add(1)
			time.Sleep(50 * time.Millisecond)
			return i, nil
		}
	}
	// Task 1 fails quickly
	tasks[1] = func(ctx context.Context) (any, error) {
		time.Sleep(10 * time.Millisecond)
		return nil, fmt.Errorf("task error")
	}

	results, err := Run(context.Background(), tasks, 1)
	if err == nil {
		t.Fatal("expected error")
	}
	if results != nil {
		t.Fatalf("results should be nil on error, got %v", results)
	}
	// Only tasks 0 and 1 should have started (task 1 fails, context cancelled)
	n := started.Load()
	if n > 2 {
		t.Fatalf("started %d tasks, expected <= 2 (fail-fast should prevent 2,3,4)", n)
	}
}

func TestRun_ContextCancellation(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 50*time.Millisecond)
	defer cancel()

	tasks := make([]Task, 5)
	for i := range tasks {
		tasks[i] = func(ctx context.Context) (any, error) {
			time.Sleep(100 * time.Millisecond)
			return i, nil
		}
	}

	_, err := Run(ctx, tasks, 2)
	if err == nil {
		t.Fatal("expected error from cancelled context")
	}
	if !errors.Is(err, context.DeadlineExceeded) && !errors.Is(err, context.Canceled) {
		t.Fatalf("expected context error, got: %v", err)
	}
}

func TestRun_PreservesOrder(t *testing.T) {
	tasks := make([]Task, 10)
	// Introduce variable delays but results must be in order
	for i := range tasks {
		d := time.Duration(50-i*3) * time.Millisecond
		tasks[i] = func(ctx context.Context) (any, error) {
			time.Sleep(d)
			return i * 10, nil
		}
	}
	results, err := Run(context.Background(), tasks, 3)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	for i, res := range results {
		if res != int64(i*10) {
			t.Fatalf("results[%d] = %v, want %d", i, res, i*10)
		}
	}
}

func TestRun_NoGoroutineLeaks(t *testing.T) {
	// Run many short tasks and verify all complete
	tasks := make([]Task, 100)
	for i := range tasks {
		tasks[i] = func(ctx context.Context) (any, error) {
			return i, nil
		}
	}
	results, err := Run(context.Background(), tasks, 10)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(results) != 100 {
		t.Fatalf("len(results) = %d, want 100", len(results))
	}
	for i, res := range results {
		if res != i {
			t.Fatalf("results[%d] = %v, want %d", i, res, i)
		}
	}
}
