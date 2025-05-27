package app

import (
	"encoding/json"
	"log"
	"sync"
	"time"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var wsLogger = log.New(log.Writer(), "kled.websocket_state: ", log.LstdFlags)

type StateType string

const (
	StateTypeTask StateType = "task"
	StateTypeAgent StateType = "agent"
	StateTypeLifecycle StateType = "lifecycle"
	StateTypeShared StateType = "shared"
)

type SharedStateConsumer struct {
	Connection *websocket.Conn
	StateType StateType
	StateID string
	ConnectionID string
	Send chan []byte
	Closed bool
	ClosedMutex sync.Mutex
}

type ConnectionMap struct {
	Connections map[string][]*SharedStateConsumer
	Mutex       sync.RWMutex
}

var connections = ConnectionMap{
	Connections: make(map[string][]*SharedStateConsumer),
}

func NewSharedStateConsumer(conn *websocket.Conn, stateType StateType, stateID string) *SharedStateConsumer {
	connectionID := uuid.New().String()
	consumer := &SharedStateConsumer{
		Connection:   conn,
		StateType:    stateType,
		StateID:      stateID,
		ConnectionID: connectionID,
		Send:         make(chan []byte, 256),
		Closed:       false,
	}

	key := string(stateType) + ":" + stateID
	connections.Mutex.Lock()
	if _, ok := connections.Connections[key]; !ok {
		connections.Connections[key] = make([]*SharedStateConsumer, 0)
	}
	connections.Connections[key] = append(connections.Connections[key], consumer)
	connections.Mutex.Unlock()

	go consumer.writePump()
	go consumer.readPump()

	initialState := consumer.GetInitialState()
	if initialState != nil {
		stateUpdateMsg := map[string]interface{}{
			"type":       "state_update",
			"state_type": stateType,
			"state_id":   stateID,
			"data":       initialState,
		}
		msgBytes, err := json.Marshal(stateUpdateMsg)
		if err == nil {
			consumer.Send <- msgBytes
		}
	}

	wsLogger.Printf("WebSocket connection established for %s state with ID %s", stateType, stateID)
	return consumer
}

func (c *SharedStateConsumer) Close() {
	c.ClosedMutex.Lock()
	if c.Closed {
		c.ClosedMutex.Unlock()
		return
	}
	c.Closed = true
	c.ClosedMutex.Unlock()

	close(c.Send)

	key := string(c.StateType) + ":" + c.StateID
	connections.Mutex.Lock()
	if conns, ok := connections.Connections[key]; ok {
		newConns := make([]*SharedStateConsumer, 0)
		for _, conn := range conns {
			if conn.ConnectionID != c.ConnectionID {
				newConns = append(newConns, conn)
			}
		}
		if len(newConns) == 0 {
			delete(connections.Connections, key)
		} else {
			connections.Connections[key] = newConns
		}
	}
	connections.Mutex.Unlock()

	wsLogger.Printf("WebSocket connection closed for %s state with ID %s", c.StateType, c.StateID)
}

func (c *SharedStateConsumer) readPump() {
	defer func() {
		c.Close()
	}()

	c.Connection.SetReadLimit(512 * 1024) // 512KB
	c.Connection.SetReadDeadline(time.Now().Add(60 * time.Second))
	c.Connection.SetPongHandler(func(string) error {
		c.Connection.SetReadDeadline(time.Now().Add(60 * time.Second))
		return nil
	})

	for {
		_, message, err := c.Connection.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				wsLogger.Printf("Error reading message: %v", err)
			}
			break
		}

		c.handleMessage(message)
	}
}

func (c *SharedStateConsumer) writePump() {
	ticker := time.NewTicker(30 * time.Second)
	defer func() {
		ticker.Stop()
		c.Connection.Close()
	}()

	for {
		select {
		case message, ok := <-c.Send:
			c.Connection.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				c.Connection.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.Connection.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			n := len(c.Send)
			for i := 0; i < n; i++ {
				w.Write([]byte{'\n'})
				w.Write(<-c.Send)
			}

			if err := w.Close(); err != nil {
				return
			}
		case <-ticker.C:
			c.Connection.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if err := c.Connection.WriteMessage(websocket.PingMessage, nil); err != nil {
				return
			}
		}
	}
}

func (c *SharedStateConsumer) handleMessage(message []byte) {
	var data map[string]interface{}
	if err := json.Unmarshal(message, &data); err != nil {
		wsLogger.Printf("Failed to decode JSON message: %v", err)
		return
	}

	messageType, ok := data["type"].(string)
	if !ok {
		wsLogger.Printf("Message missing 'type' field")
		return
	}

	switch messageType {
	case "update_state":
		stateData, ok := data["data"].(map[string]interface{})
		if !ok {
			wsLogger.Printf("Update state message missing 'data' field")
			return
		}

		success := c.UpdateState(stateData)
		if success {
			c.BroadcastStateUpdate(stateData)
		}

	case "get_state":
		state := c.GetInitialState()
		stateUpdateMsg := map[string]interface{}{
			"type":       "state_update",
			"state_type": c.StateType,
			"state_id":   c.StateID,
			"data":       state,
		}
		msgBytes, err := json.Marshal(stateUpdateMsg)
		if err == nil {
			c.Send <- msgBytes
		}

	default:
		wsLogger.Printf("Unknown message type: %s", messageType)
	}
}

func (c *SharedStateConsumer) GetInitialState() map[string]interface{} {
	try := func() (map[string]interface{}, error) {
		grpcBridgeModule, err := core.ImportPythonModule("apps.app.grpc_bridge")
		if err != nil {
			return nil, err
		}

		grpcBridge, err := grpcBridgeModule.GetAttr("grpc_bridge")
		if err != nil {
			return nil, err
		}

		getState, err := grpcBridge.GetAttr("get_state")
		if err != nil {
			return nil, err
		}

		response, err := getState.Call(string(c.StateType), c.StateID)
		if err != nil {
			return nil, err
		}

		responseMap, err := core.PyObjectToMap(response)
		if err != nil {
			return nil, err
		}

		if data, ok := responseMap["data"].(map[string]interface{}); ok {
			return data, nil
		}

		return nil, nil
	}

	result, err := try()
	if err != nil {
		wsLogger.Printf("Error getting initial state: %v", err)
		return nil
	}

	return result
}

func (c *SharedStateConsumer) UpdateState(data map[string]interface{}) bool {
	try := func() (bool, error) {
		grpcBridgeModule, err := core.ImportPythonModule("apps.app.grpc_bridge")
		if err != nil {
			return false, err
		}

		grpcBridge, err := grpcBridgeModule.GetAttr("grpc_bridge")
		if err != nil {
			return false, err
		}

		updateState, err := grpcBridge.GetAttr("update_state")
		if err != nil {
			return false, err
		}

		pyData, err := core.MapToPyObject(data)
		if err != nil {
			return false, err
		}

		response, err := updateState.Call(string(c.StateType), c.StateID, pyData)
		if err != nil {
			return false, err
		}

		responseMap, err := core.PyObjectToMap(response)
		if err != nil {
			return false, err
		}

		if status, ok := responseMap["status"].(string); ok && status == "success" {
			return true, nil
		}

		return false, nil
	}

	result, err := try()
	if err != nil {
		wsLogger.Printf("Error updating state: %v", err)
		return false
	}

	return result
}

func (c *SharedStateConsumer) BroadcastStateUpdate(data map[string]interface{}) {
	key := string(c.StateType) + ":" + c.StateID
	stateUpdateMsg := map[string]interface{}{
		"type":       "state_update",
		"state_type": c.StateType,
		"state_id":   c.StateID,
		"data":       data,
	}
	msgBytes, err := json.Marshal(stateUpdateMsg)
	if err != nil {
		wsLogger.Printf("Error marshaling state update: %v", err)
		return
	}

	connections.Mutex.RLock()
	if conns, ok := connections.Connections[key]; ok {
		for _, conn := range conns {
			select {
			case conn.Send <- msgBytes:
			default:
				conn.Close()
			}
		}
	}
	connections.Mutex.RUnlock()
}

func GetSharedState(stateID string) map[string]interface{} {
	if stateID == "" {
		stateID = "default"
	}

	try := func() (map[string]interface{}, error) {
		grpcBridgeModule, err := core.ImportPythonModule("apps.app.grpc_bridge")
		if err != nil {
			return nil, err
		}

		grpcBridge, err := grpcBridgeModule.GetAttr("grpc_bridge")
		if err != nil {
			return nil, err
		}

		getState, err := grpcBridge.GetAttr("get_state")
		if err != nil {
			return nil, err
		}

		response, err := getState.Call(string(StateTypeShared), stateID)
		if err != nil {
			return nil, err
		}

		responseMap, err := core.PyObjectToMap(response)
		if err != nil {
			return nil, err
		}

		if data, ok := responseMap["data"].(map[string]interface{}); ok {
			return data, nil
		}

		return nil, nil
	}

	result, err := try()
	if err != nil {
		wsLogger.Printf("Error getting shared state: %v", err)
		return nil
	}

	return result
}

func UpdateSharedState(stateID string, data map[string]interface{}) bool {
	if stateID == "" {
		stateID = "default"
	}

	try := func() (bool, error) {
		grpcBridgeModule, err := core.ImportPythonModule("apps.app.grpc_bridge")
		if err != nil {
			return false, err
		}

		grpcBridge, err := grpcBridgeModule.GetAttr("grpc_bridge")
		if err != nil {
			return false, err
		}

		updateState, err := grpcBridge.GetAttr("update_state")
		if err != nil {
			return false, err
		}

		pyData, err := core.MapToPyObject(data)
		if err != nil {
			return false, err
		}

		response, err := updateState.Call(string(StateTypeShared), stateID, pyData)
		if err != nil {
			return false, err
		}

		responseMap, err := core.PyObjectToMap(response)
		if err != nil {
			return false, err
		}

		if status, ok := responseMap["status"].(string); ok && status == "success" {
			key := string(StateTypeShared) + ":" + stateID
			stateUpdateMsg := map[string]interface{}{
				"type":       "state_update",
				"state_type": StateTypeShared,
				"state_id":   stateID,
				"data":       data,
			}
			msgBytes, err := json.Marshal(stateUpdateMsg)
			if err != nil {
				wsLogger.Printf("Error marshaling state update: %v", err)
				return true, nil
			}

			connections.Mutex.RLock()
			if conns, ok := connections.Connections[key]; ok {
				for _, conn := range conns {
					select {
					case conn.Send <- msgBytes:
					default:
						conn.Close()
					}
				}
			}
			connections.Mutex.RUnlock()

			return true, nil
		}

		return false, nil
	}

	result, err := try()
	if err != nil {
		wsLogger.Printf("Error updating shared state: %v", err)
		return false
	}

	return result
}
