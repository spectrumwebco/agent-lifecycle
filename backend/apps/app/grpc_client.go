package app

import (
	"context"
	"log"
	"os"
	"sync"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "github.com/spectrumwebco/agent_runtime/backend/protos/gen/go/agent_bridge"
)

var logger = log.New(os.Stdout, "[AgentBridgeClient] ", log.LstdFlags)

type AgentBridgeClient struct {
	address string
	conn    *grpc.ClientConn
	client  pb.AgentBridgeClient
	mu      sync.Mutex
}

func NewAgentBridgeClient(address string) *AgentBridgeClient {
	if address == "" {
		address = os.Getenv("GRPC_BRIDGE_ADDRESS")
		if address == "" {
			address = "localhost:50051"
		}
	}

	return &AgentBridgeClient{
		address: address,
	}
}

func (c *AgentBridgeClient) Connect() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.conn != nil {
		return nil
	}

	var err error
	c.conn, err = grpc.Dial(c.address, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		logger.Printf("Failed to connect to gRPC bridge: %v", err)
		return err
	}

	c.client = pb.NewAgentBridgeClient(c.conn)
	logger.Printf("Connected to gRPC bridge at %s", c.address)
	return nil
}

func (c *AgentBridgeClient) Close() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.conn != nil {
		err := c.conn.Close()
		c.conn = nil
		c.client = nil
		return err
	}
	return nil
}

func (c *AgentBridgeClient) SendEvent(eventType string, data map[string]string) map[string]interface{} {
	c.mu.Lock()
	if c.client == nil {
		c.mu.Unlock()
		if err := c.Connect(); err != nil {
			return map[string]interface{}{
				"success": false,
				"message": err.Error(),
			}
		}
		c.mu.Lock()
	}
	client := c.client
	c.mu.Unlock()

	req := &pb.SendEventRequest{
		EventType: eventType,
		Data:      data,
	}

	resp, err := client.SendEvent(context.Background(), req)
	if err != nil {
		logger.Printf("Error sending event: %v", err)
		return map[string]interface{}{
			"success": false,
			"message": err.Error(),
		}
	}

	return map[string]interface{}{
		"success": resp.Success,
		"message": resp.Message,
	}
}

func (c *AgentBridgeClient) GetState(stateType, stateID string) map[string]interface{} {
	c.mu.Lock()
	if c.client == nil {
		c.mu.Unlock()
		if err := c.Connect(); err != nil {
			return map[string]interface{}{
				"success": false,
				"message": err.Error(),
				"state":   map[string]interface{}{},
			}
		}
		c.mu.Lock()
	}
	client := c.client
	c.mu.Unlock()

	req := &pb.GetStateRequest{
		StateType: stateType,
		StateId:   stateID,
	}

	resp, err := client.GetState(context.Background(), req)
	if err != nil {
		logger.Printf("Error getting state: %v", err)
		return map[string]interface{}{
			"success": false,
			"message": err.Error(),
			"state":   map[string]interface{}{},
		}
	}

	state := make(map[string]interface{})
	if resp.Success {
		for k, v := range resp.State {
			state[k] = v
		}
	}

	return map[string]interface{}{
		"success": resp.Success,
		"message": resp.Message,
		"state":   state,
	}
}

func (c *AgentBridgeClient) SetState(stateType, stateID string, state map[string]string) map[string]interface{} {
	c.mu.Lock()
	if c.client == nil {
		c.mu.Unlock()
		if err := c.Connect(); err != nil {
			return map[string]interface{}{
				"success": false,
				"message": err.Error(),
			}
		}
		c.mu.Lock()
	}
	client := c.client
	c.mu.Unlock()

	req := &pb.SetStateRequest{
		StateType: stateType,
		StateId:   stateID,
		State:     state,
	}

	resp, err := client.SetState(context.Background(), req)
	if err != nil {
		logger.Printf("Error setting state: %v", err)
		return map[string]interface{}{
			"success": false,
			"message": err.Error(),
		}
	}

	return map[string]interface{}{
		"success": resp.Success,
		"message": resp.Message,
	}
}

func (c *AgentBridgeClient) StreamEvents(eventTypes []string, callback func(map[string]interface{})) bool {
	c.mu.Lock()
	if c.client == nil {
		c.mu.Unlock()
		if err := c.Connect(); err != nil {
			logger.Printf("Error connecting to stream events: %v", err)
			return false
		}
		c.mu.Lock()
	}
	client := c.client
	c.mu.Unlock()

	req := &pb.StreamEventsRequest{
		EventTypes: eventTypes,
	}

	stream, err := client.StreamEvents(context.Background(), req)
	if err != nil {
		logger.Printf("Error creating stream: %v", err)
		return false
	}

	for {
		event, err := stream.Recv()
		if err != nil {
			logger.Printf("Error receiving event: %v", err)
			return false
		}

		data := make(map[string]string)
		for k, v := range event.Data {
			data[k] = v
		}

		callback(map[string]interface{}{
			"event_type": event.EventType,
			"data":       data,
			"timestamp":  event.Timestamp,
		})
	}
}

var (
	clientInstance *AgentBridgeClient
	clientOnce     sync.Once
)

func GetClient() *AgentBridgeClient {
	clientOnce.Do(func() {
		clientInstance = NewAgentBridgeClient("")
	})
	return clientInstance
}

func SendEvent(eventType string, data map[string]string) map[string]interface{} {
	return GetClient().SendEvent(eventType, data)
}

func GetState(stateType, stateID string) map[string]interface{} {
	return GetClient().GetState(stateType, stateID)
}

func SetState(stateType, stateID string, state map[string]string) map[string]interface{} {
	return GetClient().SetState(stateType, stateID, state)
}
