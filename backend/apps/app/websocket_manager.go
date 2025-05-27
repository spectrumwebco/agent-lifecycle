package app

import (
	"encoding/json"
	"log"
	"os"
	"sync"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

var wsLogger = log.New(os.Stdout, "[WebSocketManager] ", log.LstdFlags)

type WebSocketManager struct {
	consumers       map[string]core.WebSocketConsumer
	consumerGroups  map[string]map[string]bool
	eventHandlers   map[string][]func(map[string]interface{}) error
	eventStreamTask *core.Task
	mutex           sync.RWMutex
	initialized     bool
}

var instance *WebSocketManager
var once sync.Once

func GetManager() *WebSocketManager {
	once.Do(func() {
		instance = &WebSocketManager{
			consumers:      make(map[string]core.WebSocketConsumer),
			consumerGroups: make(map[string]map[string]bool),
			eventHandlers:  make(map[string][]func(map[string]interface{}) error),
			initialized:    true,
		}
	})
	return instance
}

func (m *WebSocketManager) RegisterConsumer(consumerID string, consumer core.WebSocketConsumer, groups []string) {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	m.consumers[consumerID] = consumer

	if groups != nil {
		for _, group := range groups {
			if _, ok := m.consumerGroups[group]; !ok {
				m.consumerGroups[group] = make(map[string]bool)
			}
			m.consumerGroups[group][consumerID] = true
		}
	}

	if m.eventStreamTask == nil {
		m.startEventStream()
	}
}

func (m *WebSocketManager) UnregisterConsumer(consumerID string) {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	if _, ok := m.consumers[consumerID]; ok {
		delete(m.consumers, consumerID)
	}

	for group := range m.consumerGroups {
		if _, ok := m.consumerGroups[group][consumerID]; ok {
			delete(m.consumerGroups[group], consumerID)
		}
	}

	if len(m.consumers) == 0 && m.eventStreamTask != nil {
		m.stopEventStream()
	}
}

func (m *WebSocketManager) RegisterEventHandler(eventType string, handler func(map[string]interface{}) error) {
	m.mutex.Lock()
	defer m.mutex.Unlock()

	if _, ok := m.eventHandlers[eventType]; !ok {
		m.eventHandlers[eventType] = []func(map[string]interface{}) error{}
	}
	m.eventHandlers[eventType] = append(m.eventHandlers[eventType], handler)
}

func (m *WebSocketManager) SendToConsumer(consumerID string, message map[string]interface{}) error {
	m.mutex.RLock()
	consumer, ok := m.consumers[consumerID]
	m.mutex.RUnlock()

	if !ok {
		return nil
	}

	jsonData, err := json.Marshal(message)
	if err != nil {
		return err
	}

	return consumer.Send(string(jsonData))
}

func (m *WebSocketManager) SendToGroup(group string, message map[string]interface{}) error {
	m.mutex.RLock()
	consumerIDs, ok := m.consumerGroups[group]
	m.mutex.RUnlock()

	if !ok {
		return nil
	}

	for consumerID := range consumerIDs {
		if err := m.SendToConsumer(consumerID, message); err != nil {
			wsLogger.Printf("Error sending message to consumer %s: %v", consumerID, err)
		}
	}

	return nil
}

func (m *WebSocketManager) Broadcast(message map[string]interface{}) error {
	m.mutex.RLock()
	consumerIDs := make([]string, 0, len(m.consumers))
	for consumerID := range m.consumers {
		consumerIDs = append(consumerIDs, consumerID)
	}
	m.mutex.RUnlock()

	for _, consumerID := range consumerIDs {
		if err := m.SendToConsumer(consumerID, message); err != nil {
			wsLogger.Printf("Error broadcasting message to consumer %s: %v", consumerID, err)
		}
	}

	return nil
}

func (m *WebSocketManager) startEventStream() {
	m.eventStreamTask = core.NewTask(m.eventStreamWorker)
	m.eventStreamTask.Start()
}

func (m *WebSocketManager) stopEventStream() {
	if m.eventStreamTask != nil {
		m.eventStreamTask.Cancel()
		m.eventStreamTask = nil
	}
}

func (m *WebSocketManager) eventStreamWorker() error {
	for {
		select {
		case <-m.eventStreamTask.Context().Done():
			wsLogger.Println("Event stream worker cancelled")
			return nil
		default:
			client, err := GetClient()
			if err != nil {
				wsLogger.Printf("Error getting gRPC client: %v", err)
				time.Sleep(100 * time.Millisecond)
				continue
			}

			go func() {
				if err := m.processEvents(); err != nil {
					wsLogger.Printf("Error processing events: %v", err)
				}
			}()

			time.Sleep(100 * time.Millisecond)
		}
	}
}

func (m *WebSocketManager) processEvents() error {
	client, err := GetClient()
	if err != nil {
		return err
	}

	m.mutex.RLock()
	eventTypes := make([]string, 0, len(m.eventHandlers))
	for eventType := range m.eventHandlers {
		eventTypes = append(eventTypes, eventType)
	}
	m.mutex.RUnlock()

	for _, eventType := range eventTypes {
		m.mutex.RLock()
		handlers := m.eventHandlers[eventType]
		m.mutex.RUnlock()

		for _, handler := range handlers {
			event := map[string]interface{}{
				"event_type": eventType,
				"data":       map[string]interface{}{},
				"timestamp":  time.Now().Unix(),
			}

			if err := handler(event); err != nil {
				wsLogger.Printf("Error in event handler for %s: %v", eventType, err)
			}
		}
	}

	return nil
}

func (m *WebSocketManager) SendEvent(eventType string, data map[string]interface{}) error {
	stringData := make(map[string]string)
	for k, v := range data {
		stringData[k] = core.ToString(v)
	}

	client, err := GetClient()
	if err != nil {
		return err
	}

	result, err := client.SendEvent(eventType, stringData)
	if err != nil {
		return err
	}

	if !result["success"].(bool) {
		wsLogger.Printf("Error sending event: %s", result["message"])
		return core.NewError("Error sending event: %s", result["message"])
	}

	return nil
}

func init() {
	core.RegisterFunction("get_manager", GetManager)
}
