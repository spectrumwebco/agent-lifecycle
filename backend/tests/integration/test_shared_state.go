package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

type TestData struct {
	Message   string  `json:"message"`
	Timestamp float64 `json:"timestamp"`
	Count     int     `json:"count"`
}

type WebSocketMessage struct {
	Type string      `json:"type"`
	Data interface{} `json:"data,omitempty"`
}

func WebSocketClient(wsURL string, testData TestData) bool {
	log.Printf("Connecting to WebSocket at %s", wsURL)

	c, _, err := websocket.DefaultDialer.Dial(wsURL, nil)
	if err != nil {
		log.Printf("WebSocket connection failed: %v", err)
		return false
	}
	defer c.Close()

	log.Printf("WebSocket connection established")

	getStateMsg := WebSocketMessage{
		Type: "get_state",
	}
	getStateBytes, err := json.Marshal(getStateMsg)
	if err != nil {
		log.Printf("Failed to marshal get_state message: %v", err)
		return false
	}

	err = c.WriteMessage(websocket.TextMessage, getStateBytes)
	if err != nil {
		log.Printf("Failed to send get_state message: %v", err)
		return false
	}

	_, initialStateBytes, err := c.ReadMessage()
	if err != nil {
		log.Printf("Failed to receive initial state: %v", err)
		return false
	}
	log.Printf("Received initial state: %s", string(initialStateBytes))

	updateStateMsg := WebSocketMessage{
		Type: "update_state",
		Data: testData,
	}
	updateStateBytes, err := json.Marshal(updateStateMsg)
	if err != nil {
		log.Printf("Failed to marshal update_state message: %v", err)
		return false
	}

	err = c.WriteMessage(websocket.TextMessage, updateStateBytes)
	if err != nil {
		log.Printf("Failed to send update_state message: %v", err)
		return false
	}
	log.Printf("Sent state update: %v", testData)

	_, confirmationBytes, err := c.ReadMessage()
	if err != nil {
		log.Printf("Failed to receive update confirmation: %v", err)
		return false
	}
	log.Printf("Received update confirmation: %s", string(confirmationBytes))

	time.Sleep(1 * time.Second)

	err = c.WriteMessage(websocket.TextMessage, getStateBytes)
	if err != nil {
		log.Printf("Failed to send get_state message: %v", err)
		return false
	}

	_, updatedStateBytes, err := c.ReadMessage()
	if err != nil {
		log.Printf("Failed to receive updated state: %v", err)
		return false
	}
	log.Printf("Received updated state: %s", string(updatedStateBytes))

	var response WebSocketMessage
	err = json.Unmarshal(updatedStateBytes, &response)
	if err != nil {
		log.Printf("Failed to unmarshal response: %v", err)
		return false
	}

	if response.Type == "state_update" {
		dataMap, ok := response.Data.(map[string]interface{})
		if !ok {
			log.Printf("Invalid data format in response")
			return false
		}

		if message, ok := dataMap["message"].(string); ok && message == testData.Message {
			log.Printf("WebSocket test passed: State was updated correctly")
			return true
		}
	}

	log.Printf("WebSocket test failed: State was not updated correctly")
	return false
}

func HTTPClient(httpURL string, testData TestData) bool {
	log.Printf("Connecting to HTTP API at %s", httpURL)

	resp, err := http.Get(httpURL)
	if err != nil {
		log.Printf("Failed to get initial state: %v", err)
		return false
	}
	defer resp.Body.Close()

	initialState, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read initial state: %v", err)
		return false
	}
	log.Printf("Received initial state: %s", string(initialState))

	testDataBytes, err := json.Marshal(testData)
	if err != nil {
		log.Printf("Failed to marshal test data: %v", err)
		return false
	}

	resp, err = http.Post(
		httpURL,
		"application/json",
		bytes.NewBuffer(testDataBytes),
	)
	if err != nil {
		log.Printf("Failed to update state: %v", err)
		return false
	}
	defer resp.Body.Close()

	updateResponse, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read update response: %v", err)
		return false
	}
	log.Printf("Sent state update: %v", testData)
	log.Printf("Received update response: %s", string(updateResponse))

	time.Sleep(1 * time.Second)

	resp, err = http.Get(httpURL)
	if err != nil {
		log.Printf("Failed to get updated state: %v", err)
		return false
	}
	defer resp.Body.Close()

	updatedState, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read updated state: %v", err)
		return false
	}
	log.Printf("Received updated state: %s", string(updatedState))

	var data map[string]interface{}
	err = json.Unmarshal(updatedState, &data)
	if err != nil {
		log.Printf("Failed to unmarshal response: %v", err)
		return false
	}

	if message, ok := data["message"].(string); ok && message == testData.Message {
		log.Printf("HTTP test passed: State was updated correctly")
		return true
	}

	log.Printf("HTTP test failed: State was not updated correctly")
	return false
}

func RunTests() int {
	log.Printf("Starting shared state tests")

	apiHost := os.Getenv("API_HOST")
	if apiHost == "" {
		apiHost = "localhost:8000"
	}

	wsURL := fmt.Sprintf("ws://%s/ws/state/shared/test/", apiHost)
	httpURL := fmt.Sprintf("http://%s/api/state/shared/test/", apiHost)

	testData := TestData{
		Message:   "Hello from test script",
		Timestamp: float64(time.Now().Unix()),
		Count:     1,
	}

	var wg sync.WaitGroup
	var wsResult, httpResult bool
	var wsResultMutex, httpResultMutex sync.Mutex

	wg.Add(1)
	go func() {
		defer wg.Done()
		result := HTTPClient(httpURL, testData)
		httpResultMutex.Lock()
		httpResult = result
		httpResultMutex.Unlock()
	}()

	wsResult = WebSocketClient(wsURL, testData)

	wg.Wait()

	if wsResult && httpResult {
		log.Printf("All tests passed!")
		return 0
	} else {
		log.Printf("Some tests failed")
		return 1
	}
}

func main() {
	exitCode := RunTests()
	os.Exit(exitCode)
}
