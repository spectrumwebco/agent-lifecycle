package app

import (
	"encoding/json"
	"log"
	"os"
	"sync"

	"github.com/gorilla/websocket"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var logger = log.New(os.Stdout, "[WebSocket] ", log.LstdFlags)

type AgentConsumer struct {
	conn           *websocket.Conn
	clientID       string
	taskID         string
	connected      bool
	connectedMutex sync.Mutex
}

func NewAgentConsumer(conn *websocket.Conn, clientID, taskID string) *AgentConsumer {
	return &AgentConsumer{
		conn:     conn,
		clientID: clientID,
		taskID:   taskID,
	}
}

func (c *AgentConsumer) Connect() error {
	c.connectedMutex.Lock()
	defer c.connectedMutex.Unlock()

	if c.connected {
		return nil
	}

	c.connected = true
	logger.Printf("WebSocket connection established for client %s", c.clientID)

	return c.sendMessage(map[string]interface{}{
		"type":      "connection_established",
		"message":   "Connected",
		"client_id": c.clientID,
		"task_id":   c.taskID,
	})
}

func (c *AgentConsumer) Disconnect() error {
	c.connectedMutex.Lock()
	defer c.connectedMutex.Unlock()

	if !c.connected {
		return nil
	}

	c.connected = false
	logger.Printf("WebSocket connection closed for client %s", c.clientID)

	return c.conn.Close()
}

func (c *AgentConsumer) Receive() {
	for {
		_, message, err := c.conn.ReadMessage()
		if err != nil {
			logger.Printf("Error reading message: %v", err)
			break
		}

		var data map[string]interface{}
		if err := json.Unmarshal(message, &data); err != nil {
			logger.Printf("Invalid JSON received: %s", message)
			c.sendMessage(map[string]interface{}{
				"type":    "error",
				"message": "Invalid JSON",
			})
			continue
		}

		messageType, ok := data["type"].(string)
		if !ok {
			logger.Printf("Unknown message type: %v", data["type"])
			c.sendMessage(map[string]interface{}{
				"type":    "error",
				"message": "Unknown message type",
			})
			continue
		}

		switch messageType {
		case "task_update":
			c.handleTaskUpdate(data)
		case "agent_command":
			c.handleAgentCommand(data)
		default:
			logger.Printf("Unknown message type: %s", messageType)
			c.sendMessage(map[string]interface{}{
				"type":    "error",
				"message": "Unknown message type",
			})
		}
	}
}

func (c *AgentConsumer) handleTaskUpdate(data map[string]interface{}) {
	taskID, ok := data["task_id"].(string)
	if !ok {
		c.sendMessage(map[string]interface{}{
			"type":    "error",
			"message": "Missing task_id",
		})
		return
	}

	status, _ := data["status"].(string)
	message, _ := data["message"].(string)

	core.BroadcastToGroup("task_"+taskID, map[string]interface{}{
		"type":    "task_update",
		"task_id": taskID,
		"status":  status,
		"message": message,
		"sender":  c.clientID,
	})
}

func (c *AgentConsumer) handleAgentCommand(data map[string]interface{}) {
	command, ok := data["command"].(string)
	if !ok {
		c.sendMessage(map[string]interface{}{
			"type":    "error",
			"message": "Missing command",
		})
		return
	}

	params, _ := data["params"].(map[string]interface{})

	c.sendMessage(map[string]interface{}{
		"type":    "command_received",
		"command": command,
		"params":  params,
		"message": "Command received",
	})
}

func (c *AgentConsumer) sendMessage(message map[string]interface{}) error {
	c.connectedMutex.Lock()
	defer c.connectedMutex.Unlock()

	if !c.connected {
		return nil
	}

	return c.conn.WriteJSON(message)
}

func SendTaskUpdate(taskID, status, message string) {
	core.BroadcastToGroup("task_"+taskID, map[string]interface{}{
		"type":    "task_update",
		"task_id": taskID,
		"status":  status,
		"message": message,
		"sender":  "system",
	})
}

func BroadcastMessage(message string) {
	core.BroadcastToGroup("broadcast", map[string]interface{}{
		"type":    "broadcast_message",
		"message": message,
		"sender":  "system",
	})
}
