package integrations

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var rocketmqLogger = log.New(os.Stdout, "kled.database.rocketmq: ", log.LstdFlags)

type RocketMQManager struct {
	NameServer string
	GroupID string
	producer interface{}
	consumers map[string]interface{}
	mu sync.Mutex
}

func NewRocketMQManager(nameServer, groupID string) *RocketMQManager {
	rocketmqAvailable := checkRocketMQAvailable()
	if !rocketmqAvailable {
		rocketmqLogger.Printf("RocketMQ Go SDK not installed. Using mock client.")
	}

	rocketmqConfig := db.GetSettingMap("ROCKETMQ_CONFIG")

	if nameServer == "" {
		nameServer = rocketmqConfig["name_server"]
		if nameServer == "" {
			nameServer = os.Getenv("ROCKETMQ_NAME_SERVER")
		}
	}

	if groupID == "" {
		groupID = rocketmqConfig["group_id"]
		if groupID == "" {
			groupID = os.Getenv("ROCKETMQ_GROUP_ID")
		}
	}

	if nameServer == "" {
		rocketmqLogger.Printf("RocketMQ name server not provided. Using mock client.")
	}

	return &RocketMQManager{
		NameServer: nameServer,
		GroupID:    groupID,
		consumers:  make(map[string]interface{}),
	}
}

func checkRocketMQAvailable() bool {
	script := `
import os
import sys
try:
    from rocketmq.client import Producer, PushConsumer, ConsumeStatus
    print("true")
except ImportError:
    print("false")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return false
	}

	return strings.TrimSpace(string(output)) == "true"
}

func (m *RocketMQManager) createProducer() interface{} {
	rocketmqAvailable := checkRocketMQAvailable()
	if !rocketmqAvailable {
		return nil
	}

	if m.NameServer == "" || m.GroupID == "" {
		rocketmqLogger.Printf("RocketMQ name server or group ID not provided. Returning nil.")
		return nil
	}

	script := fmt.Sprintf(`
import os
import sys
import json
try:
    from rocketmq.client import Producer
    producer = Producer("%s")
    producer.set_name_server_address("%s")
    producer.start()
    print(json.dumps({"status": "success", "producer_id": id(producer)}))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
`, m.GroupID, m.NameServer)

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		rocketmqLogger.Printf("Error creating RocketMQ producer: %v", err)
		return nil
	}

	var result struct {
		Status    string `json:"status"`
		ProducerID int    `json:"producer_id"`
		Message   string `json:"message"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		rocketmqLogger.Printf("Error unmarshaling producer result: %v", err)
		return nil
	}

	if result.Status != "success" {
		rocketmqLogger.Printf("Error creating RocketMQ producer: %s", result.Message)
		return nil
	}

	rocketmqLogger.Printf("RocketMQ producer initialized with name server: %s", m.NameServer)
	return result.ProducerID
}

func (m *RocketMQManager) createConsumer(topic string, callback func([]byte) bool) interface{} {
	rocketmqAvailable := checkRocketMQAvailable()
	if !rocketmqAvailable {
		return nil
	}

	if m.NameServer == "" || m.GroupID == "" {
		rocketmqLogger.Printf("RocketMQ name server or group ID not provided. Returning nil.")
		return nil
	}

	callbackID := fmt.Sprintf("callback_%d", time.Now().UnixNano())

	callbackRegistry[callbackID] = callback

	script := fmt.Sprintf(`
import os
import sys
import json
import ctypes

try:
    from rocketmq.client import PushConsumer, ConsumeStatus

    # Create consumer
    consumer = PushConsumer("%s")
    consumer.set_name_server_address("%s")

    # Define callback function
    def _callback(msg):
        try:
            # Call Go callback function
            result = call_go_callback("%s", msg.body)
            return ConsumeStatus.CONSUME_SUCCESS if result else ConsumeStatus.RECONSUME_LATER
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}))
            return ConsumeStatus.RECONSUME_LATER

    # Subscribe to topic
    consumer.subscribe("%s", _callback)
    consumer.start()

    print(json.dumps({"status": "success", "consumer_id": id(consumer)}))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
`, m.GroupID, m.NameServer, callbackID, topic)

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		rocketmqLogger.Printf("Error creating RocketMQ consumer: %v", err)
		return nil
	}

	var result struct {
		Status     string `json:"status"`
		ConsumerID int    `json:"consumer_id"`
		Message    string `json:"message"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		rocketmqLogger.Printf("Error unmarshaling consumer result: %v", err)
		return nil
	}

	if result.Status != "success" {
		rocketmqLogger.Printf("Error creating RocketMQ consumer: %s", result.Message)
		return nil
	}

	rocketmqLogger.Printf("RocketMQ consumer initialized for topic: %s", topic)
	return result.ConsumerID
}

var callbackRegistry = make(map[string]func([]byte) bool)

func CallGoCallback(callbackID string, data []byte) bool {
	if callback, ok := callbackRegistry[callbackID]; ok {
		return callback(data)
	}
	return false
}

func (m *RocketMQManager) GetProducer() interface{} {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.producer == nil {
		m.producer = m.createProducer()
	}

	return m.producer
}

func (m *RocketMQManager) SendMessage(topic string, message interface{}, tags, keys string) bool {
	producer := m.GetProducer()
	if producer == nil {
		rocketmqLogger.Printf("RocketMQ producer not initialized. Returning false.")
		return false
	}

	var messageBytes []byte
	switch msg := message.(type) {
	case []byte:
		messageBytes = msg
	case string:
		messageBytes = []byte(msg)
	case map[string]interface{}:
		jsonBytes, err := json.Marshal(msg)
		if err != nil {
			rocketmqLogger.Printf("Error marshaling message to JSON: %v", err)
			return false
		}
		messageBytes = jsonBytes
	default:
		jsonBytes, err := json.Marshal(message)
		if err != nil {
			rocketmqLogger.Printf("Error marshaling message to JSON: %v", err)
			return false
		}
		messageBytes = jsonBytes
	}

	script := fmt.Sprintf(`
import os
import sys
import json
import base64
try:
    from rocketmq.client import Message, Producer
    
    # Get producer
    producer = Producer._producers.get(%d)
    if not producer:
        print(json.dumps({"status": "error", "message": "Producer not found"}))
        sys.exit(1)
    
    # Create message
    msg = Message("%s")
    msg.set_body(base64.b64decode("%s"))
    
    if "%s":
        msg.set_tags("%s")
    
    if "%s":
        msg.set_keys("%s")
    
    # Send message
    send_result = producer.send_sync(msg)
    
    if send_result.status:
        print(json.dumps({"status": "success", "msg_id": send_result.msg_id}))
    else:
        print(json.dumps({"status": "error", "message": str(send_result.status)}))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
`, producer, topic, messageBytes, tags, tags, keys, keys)

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		rocketmqLogger.Printf("Error sending message to RocketMQ: %v", err)
		return false
	}

	var result struct {
		Status  string `json:"status"`
		MsgID   string `json:"msg_id"`
		Message string `json:"message"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		rocketmqLogger.Printf("Error unmarshaling send result: %v", err)
		return false
	}

	if result.Status != "success" {
		rocketmqLogger.Printf("Error sending message to RocketMQ: %s", result.Message)
		return false
	}

	rocketmqLogger.Printf("Sent message to RocketMQ topic %s: %s", topic, result.MsgID)
	return true
}

func (m *RocketMQManager) SendJSON(topic string, data map[string]interface{}, tags, keys string) bool {
	jsonBytes, err := json.Marshal(data)
	if err != nil {
		rocketmqLogger.Printf("Error marshaling data to JSON: %v", err)
		return false
	}

	return m.SendMessage(topic, jsonBytes, tags, keys)
}

func (m *RocketMQManager) Subscribe(topic string, callback func([]byte) bool) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.consumers[topic]; ok {
		rocketmqLogger.Printf("Already subscribed to RocketMQ topic: %s", topic)
		return true
	}

	consumer := m.createConsumer(topic, callback)
	if consumer == nil {
		return false
	}

	m.consumers[topic] = consumer
	return true
}

func (m *RocketMQManager) Unsubscribe(topic string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	consumer, ok := m.consumers[topic]
	if !ok {
		rocketmqLogger.Printf("Not subscribed to RocketMQ topic: %s", topic)
		return true
	}

	script := fmt.Sprintf(`
import os
import sys
import json
try:
    from rocketmq.client import PushConsumer
    
    # Get consumer
    consumer = PushConsumer._consumers.get(%d)
    if not consumer:
        print(json.dumps({"status": "error", "message": "Consumer not found"}))
        sys.exit(1)
    
    # Shutdown consumer
    consumer.shutdown()
    print(json.dumps({"status": "success"}))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
`, consumer)

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		rocketmqLogger.Printf("Error unsubscribing from RocketMQ topic: %v", err)
		return false
	}

	var result struct {
		Status  string `json:"status"`
		Message string `json:"message"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		rocketmqLogger.Printf("Error unmarshaling unsubscribe result: %v", err)
		return false
	}

	if result.Status != "success" {
		rocketmqLogger.Printf("Error unsubscribing from RocketMQ topic: %s", result.Message)
		return false
	}

	delete(m.consumers, topic)
	return true
}

func (m *RocketMQManager) Shutdown() bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	success := true

	for topic, consumer := range m.consumers {
		script := fmt.Sprintf(`
import os
import sys
import json
try:
    from rocketmq.client import PushConsumer
    
    # Get consumer
    consumer = PushConsumer._consumers.get(%d)
    if not consumer:
        print(json.dumps({"status": "error", "message": "Consumer not found"}))
        sys.exit(1)
    
    # Shutdown consumer
    consumer.shutdown()
    print(json.dumps({"status": "success"}))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
`, consumer)

		cmd := db.ExecutePythonScript(script)
		output, err := cmd.CombinedOutput()
		if err != nil {
			rocketmqLogger.Printf("Error shutting down RocketMQ consumer for topic %s: %v", topic, err)
			success = false
			continue
		}

		var result struct {
			Status  string `json:"status"`
			Message string `json:"message"`
		}
		if err := json.Unmarshal(output, &result); err != nil {
			rocketmqLogger.Printf("Error unmarshaling shutdown result: %v", err)
			success = false
			continue
		}

		if result.Status != "success" {
			rocketmqLogger.Printf("Error shutting down RocketMQ consumer for topic %s: %s", topic, result.Message)
			success = false
			continue
		}

		delete(m.consumers, topic)
	}

	if m.producer != nil {
		script := fmt.Sprintf(`
import os
import sys
import json
try:
    from rocketmq.client import Producer
    
    # Get producer
    producer = Producer._producers.get(%d)
    if not producer:
        print(json.dumps({"status": "error", "message": "Producer not found"}))
        sys.exit(1)
    
    # Shutdown producer
    producer.shutdown()
    print(json.dumps({"status": "success"}))
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
`, m.producer)

		cmd := db.ExecutePythonScript(script)
		output, err := cmd.CombinedOutput()
		if err != nil {
			rocketmqLogger.Printf("Error shutting down RocketMQ producer: %v", err)
			success = false
		} else {
			var result struct {
				Status  string `json:"status"`
				Message string `json:"message"`
			}
			if err := json.Unmarshal(output, &result); err != nil {
				rocketmqLogger.Printf("Error unmarshaling shutdown result: %v", err)
				success = false
			} else if result.Status != "success" {
				rocketmqLogger.Printf("Error shutting down RocketMQ producer: %s", result.Message)
				success = false
			}
		}

		m.producer = nil
	}

	return success
}

type MockRocketMQManager struct {
	messages map[string][]map[string]interface{}
	callbacks map[string][]func([]byte) bool
	mu sync.Mutex
}

func NewMockRocketMQManager() *MockRocketMQManager {
	return &MockRocketMQManager{
		messages:  make(map[string][]map[string]interface{}),
		callbacks: make(map[string][]func([]byte) bool),
	}
}

func (m *MockRocketMQManager) SendMessage(topic string, message interface{}, tags, keys string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.messages[topic]; !ok {
		m.messages[topic] = make([]map[string]interface{}, 0)
	}

	var messageStr string
	switch msg := message.(type) {
	case []byte:
		messageStr = string(msg)
	case string:
		messageStr = msg
	case map[string]interface{}:
		jsonBytes, err := json.Marshal(msg)
		if err != nil {
			rocketmqLogger.Printf("Error marshaling message to JSON: %v", err)
			return false
		}
		messageStr = string(jsonBytes)
	default:
		jsonBytes, err := json.Marshal(message)
		if err != nil {
			rocketmqLogger.Printf("Error marshaling message to JSON: %v", err)
			return false
		}
		messageStr = string(jsonBytes)
	}

	msg := map[string]interface{}{
		"message":   messageStr,
		"tags":      tags,
		"keys":      keys,
		"timestamp": time.Now().Unix(),
	}

	m.messages[topic] = append(m.messages[topic], msg)

	if callbacks, ok := m.callbacks[topic]; ok {
		for _, callback := range callbacks {
			go func(cb func([]byte) bool, msg string) {
				cb([]byte(msg))
			}(callback, messageStr)
		}
	}

	return true
}

func (m *MockRocketMQManager) SendJSON(topic string, data map[string]interface{}, tags, keys string) bool {
	jsonBytes, err := json.Marshal(data)
	if err != nil {
		rocketmqLogger.Printf("Error marshaling data to JSON: %v", err)
		return false
	}

	return m.SendMessage(topic, jsonBytes, tags, keys)
}

func (m *MockRocketMQManager) Subscribe(topic string, callback func([]byte) bool) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.callbacks[topic]; !ok {
		m.callbacks[topic] = make([]func([]byte) bool, 0)
	}

	m.callbacks[topic] = append(m.callbacks[topic], callback)
	return true
}

func (m *MockRocketMQManager) Unsubscribe(topic string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, ok := m.callbacks[topic]; ok {
		delete(m.callbacks, topic)
	}

	return true
}

func (m *MockRocketMQManager) GetMessages(topic string) []map[string]interface{} {
	m.mu.Lock()
	defer m.mu.Unlock()

	if messages, ok := m.messages[topic]; ok {
		return messages
	}

	return make([]map[string]interface{}, 0)
}

func (m *MockRocketMQManager) ClearMessages(topic string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	if topic != "" {
		if _, ok := m.messages[topic]; ok {
			m.messages[topic] = make([]map[string]interface{}, 0)
		}
	} else {
		m.messages = make(map[string][]map[string]interface{})
	}

	return true
}

func (m *MockRocketMQManager) Shutdown() bool {
	m.mu.Lock()
	defer m.mu.Unlock()

	m.messages = make(map[string][]map[string]interface{})
	m.callbacks = make(map[string][]func([]byte) bool)

	return true
}

var RocketMQAvailable = checkRocketMQAvailable()

var rocketmqManager interface{}

func GetRocketMQManager() interface{} {
	if rocketmqManager == nil {
		if RocketMQAvailable {
			rocketmqManager = NewRocketMQManager("", "")
		} else {
			rocketmqManager = NewMockRocketMQManager()
		}
	}

	return rocketmqManager
}

func ExecutePythonRocketMQMethod(methodName string, args ...interface{}) (interface{}, error) {
	argsJSON, err := json.Marshal(args)
	if err != nil {
		return nil, fmt.Errorf("error marshaling args: %v", err)
	}

	script := fmt.Sprintf(`
import os
import django
import json
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_api.settings')
django.setup()

from backend.db.integrations.rocketmq import rocketmq_manager

method = getattr(rocketmq_manager, '%s', None)
if not method:
    print(json.dumps({"error": "Method not found"}))
    sys.exit(1)

args = json.loads('%s')
result = method(*args)
print(json.dumps({"result": result}))
`, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("error executing Python RocketMQ method: %v", err)
	}

	var result struct {
		Result interface{} `json:"result"`
		Error  string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("error unmarshaling result: %v", err)
	}

	if result.Error != "" {
		return nil, fmt.Errorf("Python RocketMQ error: %s", result.Error)
	}

	return result.Result, nil
}
