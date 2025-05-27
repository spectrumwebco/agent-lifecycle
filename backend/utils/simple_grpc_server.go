package utils

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/google/uuid"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/reflection"
	"google.golang.org/grpc/status"

	"github.com/spectrumwebco/agent_runtime/api/generated/protos"
)

type Task struct {
	ID      string
	Status  string
	Prompt  string
	Context map[string]string
	Tools   []string
	Result  string
	Events  []string
	mu      sync.Mutex
}

type AgentServiceServer struct {
	protos.UnimplementedAgentServiceServer
	tasks map[string]*Task
	mu    sync.Mutex
}

func NewAgentServiceServer() *AgentServiceServer {
	return &AgentServiceServer{
		tasks: make(map[string]*Task),
	}
}

func (s *AgentServiceServer) ExecuteTask(ctx context.Context, req *protos.ExecuteTaskRequest) (*protos.ExecuteTaskResponse, error) {
	log.Printf("Received ExecuteTask request with prompt: %s", req.Prompt)

	taskID := uuid.New().String()

	task := &Task{
		ID:      taskID,
		Status:  "running",
		Prompt:  req.Prompt,
		Context: req.Context,
		Tools:   req.Tools,
		Result:  "",
		Events:  []string{"Task created"},
	}

	s.mu.Lock()
	s.tasks[taskID] = task
	s.mu.Unlock()

	go s.executeTaskAsync(task)

	return &protos.ExecuteTaskResponse{
		TaskId:  taskID,
		Status:  "accepted",
		Message: "Task submitted for execution",
	}, nil
}

func (s *AgentServiceServer) GetTaskStatus(ctx context.Context, req *protos.GetTaskStatusRequest) (*protos.GetTaskStatusResponse, error) {
	log.Printf("Received GetTaskStatus request for task: %s", req.TaskId)

	taskID := req.TaskId

	s.mu.Lock()
	task, exists := s.tasks[taskID]
	s.mu.Unlock()

	if !exists {
		return nil, status.Errorf(codes.NotFound, "Task %s not found", taskID)
	}

	task.mu.Lock()
	defer task.mu.Unlock()

	return &protos.GetTaskStatusResponse{
		TaskId:  task.ID,
		Status:  task.Status,
		Result:  task.Result,
		Events:  task.Events,
	}, nil
}

func (s *AgentServiceServer) CancelTask(ctx context.Context, req *protos.CancelTaskRequest) (*protos.CancelTaskResponse, error) {
	log.Printf("Received CancelTask request for task: %s", req.TaskId)

	taskID := req.TaskId

	s.mu.Lock()
	task, exists := s.tasks[taskID]
	s.mu.Unlock()

	if !exists {
		return nil, status.Errorf(codes.NotFound, "Task %s not found", taskID)
	}

	task.mu.Lock()
	defer task.mu.Unlock()

	if task.Status == "running" {
		task.Status = "cancelled"
		task.Events = append(task.Events, "Task cancelled")

		return &protos.CancelTaskResponse{
			TaskId:  task.ID,
			Status:  "cancelled",
			Message: "Task cancelled successfully",
		}, nil
	}

	return &protos.CancelTaskResponse{
		TaskId:  task.ID,
		Status:  task.Status,
		Message: fmt.Sprintf("Cannot cancel task with status: %s", task.Status),
	}, nil
}

func (s *AgentServiceServer) executeTaskAsync(task *Task) {
	time.Sleep(2 * time.Second)

	task.mu.Lock()
	defer task.mu.Unlock()

	if task.Status == "cancelled" {
		return
	}

	task.Status = "completed"
	task.Result = fmt.Sprintf("Task completed successfully: %s", task.Prompt)
	task.Events = append(task.Events, "Task execution started", "Task execution completed")
}

func Serve() {
	port := os.Getenv("GRPC_SERVER_PORT")
	if port == "" {
		port = "50051"
	}

	server := grpc.NewServer()
	
	agentService := NewAgentServiceServer()
	protos.RegisterAgentServiceServer(server, agentService)
	
	reflection.Register(server)

	lis, err := net.Listen("tcp", fmt.Sprintf("[::]:%s", port))
	if err != nil {
		log.Fatalf("Failed to listen: %v", err)
	}

	go func() {
		log.Printf("gRPC server started on port %s", port)
		if err := server.Serve(lis); err != nil {
			log.Fatalf("Failed to serve: %v", err)
		}
	}()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

	sig := <-sigCh
	log.Printf("Received signal %v, stopping server...", sig)
	
	server.GracefulStop()
	log.Println("Server stopped")
}

func main() {
	Serve()
}
