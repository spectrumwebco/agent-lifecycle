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
	Message   string                 `json:"message"`
	Timestamp float64                `json:"timestamp"`
	Count     int                    `json:"count"`
	Nested    map[string]interface{} `json:"nested,omitempty"`
	ClientID  int                    `json:"client_id,omitempty"`
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

func GRPCClient(grpcURL string, testData TestData) bool {
	log.Printf("Connecting to gRPC API at %s", grpcURL)

	resp, err := http.Get(grpcURL)
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
		grpcURL,
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

	resp, err = http.Get(grpcURL)
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
		log.Printf("gRPC test passed: State was updated correctly")
		return true
	}

	log.Printf("gRPC test failed: State was not updated correctly")
	return false
}

func MultiClientTest(httpURL string) bool {
	log.Printf("Starting multi-client test")

	var clients []struct {
		ID   int
		Data TestData
	}

	for i := 0; i < 5; i++ {
		clientData := TestData{
			Message:   fmt.Sprintf("Hello from client %d", i),
			Timestamp: float64(time.Now().Unix()),
			Count:     i,
			ClientID:  i,
		}
		clients = append(clients, struct {
			ID   int
			Data TestData
		}{i, clientData})
	}

	var wg sync.WaitGroup
	updateState := func(clientID int, data TestData) {
		defer wg.Done()
		
		testDataBytes, err := json.Marshal(data)
		if err != nil {
			log.Printf("Client %d failed to marshal data: %v", clientID, err)
			return
		}

		resp, err := http.Post(
			httpURL,
			"application/json",
			bytes.NewBuffer(testDataBytes),
		)
		if err != nil {
			log.Printf("Client %d failed to update state: %v", clientID, err)
			return
		}
		defer resp.Body.Close()

		updateResponse, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Printf("Client %d failed to read update response: %v", clientID, err)
			return
		}
		
		log.Printf("Client %d sent state update: %v", clientID, data)
		log.Printf("Client %d received update response: %s", clientID, string(updateResponse))
	}

	for _, client := range clients {
		wg.Add(1)
		go updateState(client.ID, client.Data)
	}

	wg.Wait()

	resp, err := http.Get(httpURL)
	if err != nil {
		log.Printf("Failed to get final state: %v", err)
		return false
	}
	defer resp.Body.Close()

	finalState, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		log.Printf("Failed to read final state: %v", err)
		return false
	}
	log.Printf("Received final state after multi-client test: %s", string(finalState))

	var data map[string]interface{}
	err = json.Unmarshal(finalState, &data)
	if err != nil {
		log.Printf("Failed to unmarshal response: %v", err)
		return false
	}

	if _, ok := data["client_id"]; ok {
		log.Printf("Multi-client test passed: State was updated correctly")
		return true
	}

	log.Printf("Multi-client test failed: State was not updated correctly")
	return false
}

func RunTests() int {
	log.Printf("Starting shared state integration tests")

	apiHost := os.Getenv("API_HOST")
	if apiHost == "" {
		apiHost = "localhost:8000"
	}

	wsURL := fmt.Sprintf("ws://%s/ws/state/shared/integration-test/", apiHost)
	httpURL := fmt.Sprintf("http://%s/api/state/shared/integration-test/", apiHost)
	grpcURL := fmt.Sprintf("http://%s/api/grpc/state/shared/integration-test/", apiHost)

	testData := TestData{
		Message:   "Hello from integration test",
		Timestamp: float64(time.Now().Unix()),
		Count:     1,
		Nested: map[string]interface{}{
			"key1": "value1",
			"key2": "value2",
		},
	}

	httpResultCh := make(chan bool)
	grpcResultCh := make(chan bool)
	wsResultCh := make(chan bool)

	go func() {
		httpResultCh <- HTTPClient(httpURL, testData)
	}()

	go func() {
		grpcResultCh <- GRPCClient(grpcURL, testData)
	}()

	go func() {
		wsResultCh <- WebSocketClient(wsURL, testData)
	}()

	httpResult := <-httpResultCh
	grpcResult := <-grpcResultCh
	wsResult := <-wsResultCh

	multiClientResult := MultiClientTest(httpURL)

	if wsResult && httpResult && grpcResult && multiClientResult {
		log.Printf("All integration tests passed!")
		return 0
	} else {
		log.Printf("Some integration tests failed")
		return 1
	}
}

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		time.Sleep(30 * time.Second) // Timeout after 30 seconds
		cancel()
	}()

	exitCode := RunTests()

	os.Exit(exitCode)
}
