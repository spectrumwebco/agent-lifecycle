package examples

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/spectrumwebco/agent_runtime/api/generated/protos"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

type AgentRuntimeGrpcClient struct {
	serverAddress string
	conn          *grpc.ClientConn
	client        protos.AgentServiceClient
}

func NewAgentRuntimeGrpcClient(serverAddress string) (*AgentRuntimeGrpcClient, error) {
	conn, err := grpc.Dial(serverAddress, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, fmt.Errorf("failed to connect to gRPC server: %v", err)
	}

	client := protos.NewAgentServiceClient(conn)

	return &AgentRuntimeGrpcClient{
		serverAddress: serverAddress,
		conn:          conn,
		client:        client,
	}, nil
}

func (c *AgentRuntimeGrpcClient) Close() error {
	if c.conn != nil {
		return c.conn.Close()
	}
	return nil
}

func (c *AgentRuntimeGrpcClient) ExecuteTask(
	ctx context.Context,
	prompt string,
	context map[string]string,
	tools []string,
) (map[string]interface{}, error) {
	if context == nil {
		context = make(map[string]string)
	}
	if tools == nil {
		tools = make([]string, 0)
	}

	request := &protos.ExecuteTaskRequest{
		Prompt:  prompt,
		Context: context,
		Tools:   tools,
	}

	response, err := c.client.ExecuteTask(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("gRPC error: %v", err)
	}

	return map[string]interface{}{
		"task_id": response.TaskId,
		"status":  response.Status,
		"message": response.Message,
	}, nil
}

func (c *AgentRuntimeGrpcClient) GetTaskStatus(
	ctx context.Context,
	taskID string,
) (map[string]interface{}, error) {
	request := &protos.GetTaskStatusRequest{
		TaskId: taskID,
	}

	response, err := c.client.GetTaskStatus(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("gRPC error: %v", err)
	}

	return map[string]interface{}{
		"task_id": response.TaskId,
		"status":  response.Status,
		"result":  response.Result,
		"events":  response.Events,
	}, nil
}

func (c *AgentRuntimeGrpcClient) CancelTask(
	ctx context.Context,
	taskID string,
) (map[string]interface{}, error) {
	request := &protos.CancelTaskRequest{
		TaskId: taskID,
	}

	response, err := c.client.CancelTask(ctx, request)
	if err != nil {
		return nil, fmt.Errorf("gRPC error: %v", err)
	}

	return map[string]interface{}{
		"task_id": response.TaskId,
		"status":  response.Status,
		"message": response.Message,
	}, nil
}

func (c *AgentRuntimeGrpcClient) WaitForTaskCompletion(
	ctx context.Context,
	taskID string,
	timeout time.Duration,
	pollInterval time.Duration,
) (map[string]interface{}, error) {
	if timeout == 0 {
		timeout = 300 * time.Second
	}
	if pollInterval == 0 {
		pollInterval = 5 * time.Second
	}

	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()

	ticker := time.NewTicker(pollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil, fmt.Errorf("task %s did not complete within %v", taskID, timeout)
		case <-ticker.C:
			status, err := c.GetTaskStatus(ctx, taskID)
			if err != nil {
				return nil, err
			}

			statusStr, ok := status["status"].(string)
			if ok && (statusStr == "completed" || statusStr == "failed" || statusStr == "cancelled") {
				return status, nil
			}

			log.Printf("Task %s status: %s", taskID, statusStr)
		}
	}
}

func RunExample() {
	serverAddress := os.Getenv("GRPC_SERVER_ADDRESS")
	if serverAddress == "" {
		serverAddress = "localhost:50051"
	}

	log.Printf("Connecting to gRPC server at %s...", serverAddress)

	client, err := NewAgentRuntimeGrpcClient(serverAddress)
	if err != nil {
		log.Fatalf("Failed to create client: %v", err)
	}
	defer client.Close()

	log.Printf("Executing task...")

	ctx := context.Background()

	taskResponse, err := client.ExecuteTask(
		ctx,
		"Create a simple Go function to calculate factorial",
		map[string]string{"language": "go"},
		[]string{"code_generation"},
	)
	if err != nil {
		log.Fatalf("Error executing task: %v", err)
	}

	taskID, ok := taskResponse["task_id"].(string)
	if !ok {
		log.Fatalf("Invalid task ID in response")
	}

	log.Printf("Task submitted with ID: %s", taskID)
	log.Printf("Waiting for task completion...")

	finalStatus, err := client.WaitForTaskCompletion(ctx, taskID, 0, 0)
	if err != nil {
		log.Fatalf("Error waiting for task completion: %v", err)
	}

	log.Printf("Task completed with status: %s", finalStatus["status"])
	
	if result, ok := finalStatus["result"].(string); ok && result != "" {
		log.Printf("Result: %s", result)
	}

	if events, ok := finalStatus["events"].([]string); ok && len(events) > 0 {
		log.Printf("Events:")
		for _, event := range events {
			log.Printf("- %s", event)
		}
	}
}

func main() {
	RunExample()
}
