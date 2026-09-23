package main

import (
	"context"
	"sync/atomic"
	"testing"
	"time"
)

func TestRunBasic(t *testing.T) {
	ctx := context.Background()
	tasks := []Task{
		func(ctx context.Context) (any, error) { return 1, nil },
		func(ctx context.Context) (any, error) { return 2, nil },
		func(ctx context.Context) (any, error) { return 3, nil },
	}
	results, err := Run(ctx, tasks, 2)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if len(results) != 3 {
		t.Fatalf("expected 3 results, got %d", len(results))
	}
	// Check ordering
	r1, r2, r3 := results[0], results[1], results[2]
	if r1 != 1 || r2 != 2 || r3 != 3 {
		t.Fatalf("expected [1 2 3], got [%v %v %v]", r1, r2, r3)
	}
}

func TestRunEmpty(t *testing.T) {
	ctx := context.Background()
	results, err := Run(ctx, [], 2)
	if err != nil {
		t.Fatalf("expected no error, got: %v", err)
	}
	if len(results) != 0 {
		t.Fatalf("expected 0 results, got %d", len(results))
	}
}

func TestRunWorkersZero(t *testing.T) {
	ctx := context.Background()
	_, err := Run(ctx, []Task{
		func(ctx context.Context) (any, error) { return 1, nil },
	}, 0)
	if err == nil {
		t.Fatal("expected error for workers < 1")
	}
}

func TestRunWorkersNegative(t *testing.T) {
	ctx := context.Background()
	_, err := Run(ctx, []Task{
		func(ctx context.Context) (any, error) { return 1, nil },
	}, -1)
	if err == nil {
		t.Fatal("expected error for workers < 1")
	}
}

func TestRunOrderingWithErrors(t *testing.T) {
	ctx := context.Background()
	tasks := []Task{
		func(ctx context.Context) (any, error) { return 1, nil },
		func(ctx context.Context) (any, error) { return 0, errors.New("fail") },
		func(ctx context.Context) (any, error) { return 3, nil },
	}
	results, err := Run(ctx, tasks, 3)
	if err == nil {
		t.Fatal("expected error because a task failed")
	}
	if results != nil {
		t.Fatalf("expected nil results on error, got %v", results)
	}
	// The first error should be the one from task 1.
	if err.Error() != "fail" {
		t.Fatalf("expected error 'fail', got '%v'", err.Error())
	}
}

func TestRunContextCancellation(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 1*time.Millisecond)
	defer cancel()

	tasks := []Task{
		func(ctx context.Context) (any, error) {
			select {
			case <-ctx.Done():
				return 0, ctx.Err()
			case <-time.After(10 * time.Millisecond):
				return 42, nil
			}
		},
	}
	results, err := Run(ctx, tasks, 1)
	if err != ctx.Err() {
		t.Fatalf("expected ctx.Err(), got %v", err)
	}
	if results != nil {
		t.Fatalf("expected nil results, got %v", results)
	}
}

func TestRunFailFastStopsNewTasks(t *testing.T) {
	// If the first task errors, later tasks must never start.
	var started int32
	ctx := context.Background()
	tasks := []Task{
		func(ctx context.Context) (any, error) {
			atomic.AddInt32(&started, 1)
			return 0, errors.New("first error")
		},
			func(ctx context.Context) (any, error) {
			atomic.AddInt32(&started, 1)
			return 1, nil
		},
		func(ctx context.Context) (any, error) {
			atomic.AddInt32(&started, 1)
			return 2, nil
		},
	}
	results, err := Run(ctx, tasks, 3)
	if err == nil {
		t.Fatal("expected error")
	}
	if results != nil {
		t.Fatalf("expected nil results, got %v", results)
	}
	// Only the first task should have started.
	if started != 1 {
		t.Fatalf("expected 1 task to start, got %d", started)
	}
}
