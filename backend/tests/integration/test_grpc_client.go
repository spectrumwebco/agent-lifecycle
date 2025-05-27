package integration

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/status"

	"github.com/spectrumwebco/agent_runtime/api/generated/protos"
)

func TestGRPCConnection() bool {
	serverAddress := os.Getenv("GRPC_SERVER_ADDRESS")
	if serverAddress == "" {
		serverAddress = "localhost:50051"
	}
	log.Printf("Testing connection to gRPC server at %s...", serverAddress)

	conn, err := grpc.Dial(serverAddress, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Printf("Error connecting to gRPC server: %v", err)
		return false
	}
	defer conn.Close()

	client := protos.NewAgentServiceClient(conn)

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	request := &protos.ExecuteTaskRequest{
		Prompt:  "Test connection",
		Context: map[string]string{"test": "true"},
		Tools:   []string{"test"},
	}

	response, err := client.ExecuteTask(ctx, request)
	if err != nil {
		st, ok := status.FromError(err)
		if ok {
			log.Printf("RPC error: %s, %s", st.Code(), st.Message())
		} else {
			log.Printf("Error executing task: %v", err)
		}
		return false
	}

	log.Printf("Connection successful! Response: %v", response)
	return true
}

func TestTaskExecution() bool {
	serverAddress := os.Getenv("GRPC_SERVER_ADDRESS")
	if serverAddress == "" {
		serverAddress = "localhost:50051"
	}
	log.Printf("Testing task execution on gRPC server at %s...", serverAddress)

	conn, err := grpc.Dial(serverAddress, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Printf("Error connecting to gRPC server: %v", err)
		return false
	}
	defer conn.Close()

	client := protos.NewAgentServiceClient(conn)

	request := &protos.ExecuteTaskRequest{
		Prompt:  "Create a simple Go function to calculate factorial",
		Context: map[string]string{"language": "go"},
		Tools:   []string{"code_generation"},
	}

	response, err := client.ExecuteTask(context.Background(), request)
	if err != nil {
		log.Printf("Error executing task: %v", err)
		return false
	}

	log.Printf("Task submitted with ID: %s", response.TaskId)

	taskID := response.TaskId
	maxAttempts := 10
	pollInterval := 2 * time.Second

	for attempt := 0; attempt < maxAttempts; attempt++ {
		statusRequest := &protos.GetTaskStatusRequest{
			TaskId: taskID,
		}

		statusResponse, err := client.GetTaskStatus(context.Background(), statusRequest)
		if err != nil {
			log.Printf("Error getting task status: %v", err)
			return false
		}

		log.Printf("Task status: %s", statusResponse.Status)

		if statusResponse.Status == "completed" || statusResponse.Status == "failed" || statusResponse.Status == "cancelled" {
			log.Printf("Task result: %s", statusResponse.Result)
			if len(statusResponse.Events) > 0 {
				log.Printf("Task events:")
				for _, event := range statusResponse.Events {
					log.Printf("- %s", event)
				}
			}
			return true
		}

		time.Sleep(pollInterval)
	}

	log.Printf("Task did not complete within %d seconds", maxAttempts*int(pollInterval.Seconds()))
	return false
}

func TestTaskCancellation() bool {
	serverAddress := os.Getenv("GRPC_SERVER_ADDRESS")
	if serverAddress == "" {
		serverAddress = "localhost:50051"
	}
	log.Printf("Testing task cancellation on gRPC server at %s...", serverAddress)

	conn, err := grpc.Dial(serverAddress, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Printf("Error connecting to gRPC server: %v", err)
		return false
	}
	defer conn.Close()

	client := protos.NewAgentServiceClient(conn)

	request := &protos.ExecuteTaskRequest{
		Prompt:  "This is a long-running task that will be cancelled",
		Context: map[string]string{"test": "cancellation"},
		Tools:   []string{"test"},
	}

	response, err := client.ExecuteTask(context.Background(), request)
	if err != nil {
		log.Printf("Error executing task: %v", err)
		return false
	}

	taskID := response.TaskId
	log.Printf("Task submitted with ID: %s", taskID)

	time.Sleep(1 * time.Second)

	cancelRequest := &protos.CancelTaskRequest{
		TaskId: taskID,
	}

	cancelResponse, err := client.CancelTask(context.Background(), cancelRequest)
	if err != nil {
		log.Printf("Error cancelling task: %v", err)
		return false
	}

	log.Printf("Task cancellation response: %s - %s", cancelResponse.Status, cancelResponse.Message)

	statusRequest := &protos.GetTaskStatusRequest{
		TaskId: taskID,
	}

	statusResponse, err := client.GetTaskStatus(context.Background(), statusRequest)
	if err != nil {
		log.Printf("Error getting task status: %v", err)
		return false
	}

	log.Printf("Task status after cancellation: %s", statusResponse.Status)

	return statusResponse.Status == "cancelled"
}

func RunPerformanceTest() float64 {
	serverAddress := os.Getenv("GRPC_SERVER_ADDRESS")
	if serverAddress == "" {
		serverAddress = "localhost:50051"
	}
	log.Printf("Running performance test on gRPC server at %s...", serverAddress)

	conn, err := grpc.Dial(serverAddress, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Printf("Error connecting to gRPC server: %v", err)
		return -1
	}
	defer conn.Close()

	client := protos.NewAgentServiceClient(conn)

	numRequests := 10
	totalTime := 0.0

	for i := 0; i < numRequests; i++ {
		request := &protos.ExecuteTaskRequest{
			Prompt:  fmt.Sprintf("Performance test request %d", i),
			Context: map[string]string{"test": "performance"},
			Tools:   []string{"test"},
		}

		startTime := time.Now()
		_, err := client.ExecuteTask(context.Background(), request)
		if err != nil {
			log.Printf("Error executing task: %v", err)
			continue
		}
		endTime := time.Now()

		responseTime := endTime.Sub(startTime).Seconds()
		totalTime += responseTime

		log.Printf("Request %d/%d: Response time = %.4fs", i+1, numRequests, responseTime)
	}

	avgResponseTime := totalTime / float64(numRequests)
	log.Printf("Average response time over %d requests: %.4fs", numRequests, avgResponseTime)

	return avgResponseTime
}

func RunAllTests() {
	log.Printf("Starting Go gRPC server functionality tests...")

	connectionResult := TestGRPCConnection()
	if !connectionResult {
		log.Printf("Connection test failed. Make sure the Go gRPC server is running.")
		return
	}

	executionResult := TestTaskExecution()
	if executionResult {
		log.Printf("Task execution test passed!")
	} else {
		log.Printf("Task execution test did not complete successfully.")
	}

	cancellationResult := TestTaskCancellation()
	if cancellationResult {
		log.Printf("Task cancellation test passed!")
	} else {
		log.Printf("Task cancellation test did not complete successfully.")
	}

	avgResponseTime := RunPerformanceTest()
	if avgResponseTime >= 0 {
		log.Printf("Performance test completed with average response time: %.4fs", avgResponseTime)
	}

	log.Printf("All tests completed!")
}

func main() {
	RunAllTests()
}
