package app

import (
	"encoding/json"
	"log"
	"sync"

	"github.com/google/uuid"
	"github.com/gorilla/websocket"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var consumerLogger = log.New(log.Writer(), "kled.consumers: ", log.LstdFlags)

type BaseWebSocketConsumer struct {
	Connection *websocket.Conn
	ConsumerID string
	User interface{}
	Groups []string
	Send chan []byte
	Closed bool
	ClosedMutex sync.Mutex
	EventHandlers map[string]func(map[string]interface{}) error
}

func NewBaseWebSocketConsumer(conn *websocket.Conn) *BaseWebSocketConsumer {
	consumerID := uuid.New().String()
	consumer := &BaseWebSocketConsumer{
		Connection:    conn,
		ConsumerID:    consumerID,
		Groups:        make([]string, 0),
		Send:          make(chan []byte, 256),
		Closed:        false,
		EventHandlers: make(map[string]func(map[string]interface{}) error),
	}

	user := core.GetUserFromContext(conn.Context())
	consumer.User = user

	if user != nil && core.IsUserAuthenticated(user) {
		userID := core.GetUserID(user)
		consumer.Groups = append(consumer.Groups, "user_"+userID)
	}

	manager := GetManager()
	manager.RegisterConsumer(consumer.ConsumerID, consumer, consumer.Groups)

	go consumer.writePump()
	go consumer.readPump()

	connectionMsg := map[string]interface{}{
		"type":        "connection_established",
		"consumer_id": consumer.ConsumerID,
	}
	msgBytes, err := json.Marshal(connectionMsg)
	if err == nil {
		consumer.Send <- msgBytes
	}

	consumerLogger.Printf("WebSocket connection established for consumer %s", consumer.ConsumerID)
	return consumer
}

func (c *BaseWebSocketConsumer) Close() {
	c.ClosedMutex.Lock()
	if c.Closed {
		c.ClosedMutex.Unlock()
		return
	}
	c.Closed = true
	c.ClosedMutex.Unlock()

	close(c.Send)

	manager := GetManager()
	manager.UnregisterConsumer(c.ConsumerID)

	consumerLogger.Printf("WebSocket connection closed for consumer %s", c.ConsumerID)
}

func (c *BaseWebSocketConsumer) readPump() {
	defer func() {
		c.Close()
	}()

	for {
		_, message, err := c.Connection.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				consumerLogger.Printf("Error reading message: %v", err)
			}
			break
		}

		c.handleMessage(message)
	}
}

func (c *BaseWebSocketConsumer) writePump() {
	defer func() {
		c.Connection.Close()
	}()

	for {
		select {
		case message, ok := <-c.Send:
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
		}
	}
}

func (c *BaseWebSocketConsumer) handleMessage(message []byte) {
	var data map[string]interface{}
	if err := json.Unmarshal(message, &data); err != nil {
		consumerLogger.Printf("Failed to decode JSON message: %v", err)
		c.sendError("Invalid JSON")
		return
	}

	messageType, ok := data["type"].(string)
	if !ok {
		consumerLogger.Printf("Message missing 'type' field")
		c.sendError("Missing message type")
		return
	}

	if messageType == "ping" {
		pongMsg := map[string]interface{}{
			"type":      "pong",
			"timestamp": data["timestamp"],
		}
		msgBytes, err := json.Marshal(pongMsg)
		if err == nil {
			c.Send <- msgBytes
		}
		return
	}

	switch messageType {
	case "subscribe":
		c.handleSubscribe(data)
	case "unsubscribe":
		c.handleUnsubscribe(data)
	case "event":
		c.handleEvent(data)
	default:
		consumerLogger.Printf("Unknown message type: %s", messageType)
		c.sendError("Unknown message type: " + messageType)
	}
}

func (c *BaseWebSocketConsumer) handleSubscribe(data map[string]interface{}) {
	eventTypes, ok := data["event_types"].([]interface{})
	if !ok || len(eventTypes) == 0 {
		c.sendError("No event types specified")
		return
	}

	manager := GetManager()
	eventTypeStrings := make([]string, 0, len(eventTypes))

	for _, eventType := range eventTypes {
		if eventTypeStr, ok := eventType.(string); ok {
			manager.RegisterEventHandler(eventTypeStr, c.handleEventCallback)
			eventTypeStrings = append(eventTypeStrings, eventTypeStr)
		}
	}

	subscribedMsg := map[string]interface{}{
		"type":        "subscribed",
		"event_types": eventTypeStrings,
	}
	msgBytes, err := json.Marshal(subscribedMsg)
	if err == nil {
		c.Send <- msgBytes
	}
}

func (c *BaseWebSocketConsumer) handleUnsubscribe(data map[string]interface{}) {
	eventTypes, ok := data["event_types"].([]interface{})
	if !ok || len(eventTypes) == 0 {
		c.sendError("No event types specified")
		return
	}

	manager := GetManager()
	eventTypeStrings := make([]string, 0, len(eventTypes))

	for _, eventType := range eventTypes {
		if eventTypeStr, ok := eventType.(string); ok {
			manager.UnregisterEventHandler(eventTypeStr, c.handleEventCallback)
			eventTypeStrings = append(eventTypeStrings, eventTypeStr)
		}
	}

	unsubscribedMsg := map[string]interface{}{
		"type":        "unsubscribed",
		"event_types": eventTypeStrings,
	}
	msgBytes, err := json.Marshal(unsubscribedMsg)
	if err == nil {
		c.Send <- msgBytes
	}
}

func (c *BaseWebSocketConsumer) handleEvent(data map[string]interface{}) {
	eventType, ok := data["event_type"].(string)
	if !ok || eventType == "" {
		c.sendError("No event type specified")
		return
	}

	eventData, _ := data["data"].(map[string]interface{})
	if eventData == nil {
		eventData = make(map[string]interface{})
	}

	manager := GetManager()
	err := manager.SendEvent(eventType, eventData)
	if err != nil {
		c.sendError("Failed to send event: " + err.Error())
		return
	}

	eventSentMsg := map[string]interface{}{
		"type":       "event_sent",
		"event_type": eventType,
	}
	msgBytes, err := json.Marshal(eventSentMsg)
	if err == nil {
		c.Send <- msgBytes
	}
}

func (c *BaseWebSocketConsumer) handleEventCallback(event map[string]interface{}) error {
	eventMsg := map[string]interface{}{
		"type":       "event",
		"event_type": event["event_type"],
		"data":       event["data"],
		"timestamp":  event["timestamp"],
	}
	msgBytes, err := json.Marshal(eventMsg)
	if err != nil {
		return err
	}

	c.Send <- msgBytes
	return nil
}

func (c *BaseWebSocketConsumer) sendError(message string) {
	errorMsg := map[string]interface{}{
		"type":    "error",
		"message": message,
	}
	msgBytes, err := json.Marshal(errorMsg)
	if err == nil {
		c.Send <- msgBytes
	}
}

type AgentWebSocketConsumer struct {
	*BaseWebSocketConsumer
}

func NewAgentWebSocketConsumer(conn *websocket.Conn) *AgentWebSocketConsumer {
	base := NewBaseWebSocketConsumer(conn)
	consumer := &AgentWebSocketConsumer{
		BaseWebSocketConsumer: base,
	}

	consumer.Groups = append(consumer.Groups, "agent")

	manager := GetManager()
	manager.RegisterConsumer(consumer.ConsumerID, consumer, consumer.Groups)

	return consumer
}

func (c *AgentWebSocketConsumer) handleMessage(message []byte) {
	var data map[string]interface{}
	if err := json.Unmarshal(message, &data); err != nil {
		consumerLogger.Printf("Failed to decode JSON message: %v", err)
		c.sendError("Invalid JSON")
		return
	}

	messageType, ok := data["type"].(string)
	if !ok {
		consumerLogger.Printf("Message missing 'type' field")
		c.sendError("Missing message type")
		return
	}

	if messageType == "agent_command" {
		c.handleAgentCommand(data)
	} else {
		c.BaseWebSocketConsumer.handleMessage(message)
	}
}

func (c *AgentWebSocketConsumer) handleAgentCommand(data map[string]interface{}) {
	command, ok := data["command"].(string)
	if !ok || command == "" {
		c.sendError("No command specified")
		return
	}

	commandData, _ := data["data"].(map[string]interface{})
	if commandData == nil {
		commandData = make(map[string]interface{})
	}

	commandDataJSON, err := json.Marshal(commandData)
	if err != nil {
		c.sendError("Failed to marshal command data: " + err.Error())
		return
	}

	manager := GetManager()
	err = manager.SendEvent("agent_command", map[string]interface{}{
		"command":     command,
		"data":        string(commandDataJSON),
		"consumer_id": c.ConsumerID,
	})
	if err != nil {
		c.sendError("Failed to send agent command: " + err.Error())
		return
	}

	commandSentMsg := map[string]interface{}{
		"type":    "command_sent",
		"command": command,
	}
	msgBytes, err := json.Marshal(commandSentMsg)
	if err == nil {
		c.Send <- msgBytes
	}
}

type MLWebSocketConsumer struct {
	*BaseWebSocketConsumer
}

func NewMLWebSocketConsumer(conn *websocket.Conn) *MLWebSocketConsumer {
	base := NewBaseWebSocketConsumer(conn)
	consumer := &MLWebSocketConsumer{
		BaseWebSocketConsumer: base,
	}

	consumer.Groups = append(consumer.Groups, "ml")

	manager := GetManager()
	manager.RegisterConsumer(consumer.ConsumerID, consumer, consumer.Groups)

	return consumer
}

func (c *MLWebSocketConsumer) handleMessage(message []byte) {
	var data map[string]interface{}
	if err := json.Unmarshal(message, &data); err != nil {
		consumerLogger.Printf("Failed to decode JSON message: %v", err)
		c.sendError("Invalid JSON")
		return
	}

	messageType, ok := data["type"].(string)
	if !ok {
		consumerLogger.Printf("Message missing 'type' field")
		c.sendError("Missing message type")
		return
	}

	if messageType == "ml_command" {
		c.handleMLCommand(data)
	} else {
		c.BaseWebSocketConsumer.handleMessage(message)
	}
}

func (c *MLWebSocketConsumer) handleMLCommand(data map[string]interface{}) {
	command, ok := data["command"].(string)
	if !ok || command == "" {
		c.sendError("No command specified")
		return
	}

	commandData, _ := data["data"].(map[string]interface{})
	if commandData == nil {
		commandData = make(map[string]interface{})
	}

	commandDataJSON, err := json.Marshal(commandData)
	if err != nil {
		c.sendError("Failed to marshal command data: " + err.Error())
		return
	}

	manager := GetManager()
	err = manager.SendEvent("ml_command", map[string]interface{}{
		"command":     command,
		"data":        string(commandDataJSON),
		"consumer_id": c.ConsumerID,
	})
	if err != nil {
		c.sendError("Failed to send ML command: " + err.Error())
		return
	}

	commandSentMsg := map[string]interface{}{
		"type":    "command_sent",
		"command": command,
	}
	msgBytes, err := json.Marshal(commandSentMsg)
	if err == nil {
		c.Send <- msgBytes
	}
}

func GetManager() *WebSocketManager {
	return getWebSocketManager()
}

type WebSocketManager struct {
}

func (m *WebSocketManager) RegisterConsumer(consumerID string, consumer interface{}, groups []string) {
}

func (m *WebSocketManager) UnregisterConsumer(consumerID string) {
}

func (m *WebSocketManager) RegisterEventHandler(eventType string, handler func(map[string]interface{}) error) {
}

func (m *WebSocketManager) UnregisterEventHandler(eventType string, handler func(map[string]interface{}) error) {
}

func (m *WebSocketManager) SendEvent(eventType string, data map[string]interface{}) error {
	return nil
}

func getWebSocketManager() *WebSocketManager {
	return &WebSocketManager{}
}
