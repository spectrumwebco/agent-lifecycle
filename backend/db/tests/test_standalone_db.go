package tests

import (
	"fmt"
	"log"
	"os"
	"time"
)

var logger *log.Logger

func init() {
	logger = log.New(os.Stdout, "", log.LstdFlags)
	logger.SetPrefix(time.Now().Format("2006-01-02 15:04:05") + " - database-test - INFO - ")
}

type MockSupabaseClient struct {
	URL  string
	Key  string
	Data map[string][]map[string]interface{}
}

func NewMockSupabaseClient(url, key string) *MockSupabaseClient {
	if url == "" {
		url = "mock://supabase"
	}
	if key == "" {
		key = "mock-key"
	}
	
	client := &MockSupabaseClient{
		URL:  url,
		Key:  key,
		Data: make(map[string][]map[string]interface{}),
	}
	
	logger.Printf("Initialized MockSupabaseClient")
	return client
}

func (c *MockSupabaseClient) QueryTable(tableName string) []map[string]interface{} {
	if _, ok := c.Data[tableName]; !ok {
		c.Data[tableName] = []map[string]interface{}{}
	}
	return c.Data[tableName]
}

func (c *MockSupabaseClient) InsertRecord(tableName string, record map[string]interface{}) map[string]interface{} {
	if _, ok := c.Data[tableName]; !ok {
		c.Data[tableName] = []map[string]interface{}{}
	}
	
	record["id"] = len(c.Data[tableName]) + 1
	c.Data[tableName] = append(c.Data[tableName], record)
	return record
}

type MockRAGflowClient struct {
	Host string
	Port int
}

func NewMockRAGflowClient(host string, port int) *MockRAGflowClient {
	if host == "" {
		host = "localhost"
	}
	if port == 0 {
		port = 8000
	}
	
	client := &MockRAGflowClient{
		Host: host,
		Port: port,
	}
	
	logger.Printf("Initialized MockRAGflowClient")
	return client
}

func (c *MockRAGflowClient) Search(query string, topK int) map[string]interface{} {
	if topK == 0 {
		topK = 5
	}
	
	return map[string]interface{}{
		"results": []map[string]interface{}{
			{
				"content": fmt.Sprintf("Result for %s", query),
				"score":   0.9,
			},
		},
	}
}

type MockDragonflyClient struct {
	Host string
	Port int
	Data map[string]interface{}
}

func NewMockDragonflyClient(host string, port int) *MockDragonflyClient {
	if host == "" {
		host = "localhost"
	}
	if port == 0 {
		port = 6379
	}
	
	client := &MockDragonflyClient{
		Host: host,
		Port: port,
		Data: make(map[string]interface{}),
	}
	
	logger.Printf("Initialized MockDragonflyClient")
	return client
}

func (c *MockDragonflyClient) Set(key string, value interface{}) bool {
	c.Data[key] = value
	return true
}

func (c *MockDragonflyClient) Get(key string) interface{} {
	return c.Data[key]
}

type MockDorisClient struct {
	ConnectionParams map[string]interface{}
	Tables           map[string]map[string]interface{}
}

func NewMockDorisClient(connectionParams map[string]interface{}) *MockDorisClient {
	if connectionParams == nil {
		connectionParams = make(map[string]interface{})
	}
	
	client := &MockDorisClient{
		ConnectionParams: connectionParams,
		Tables:           make(map[string]map[string]interface{}),
	}
	
	logger.Printf("Initialized MockDorisClient")
	return client
}

func (c *MockDorisClient) ExecuteQuery(query string) []map[string]interface{} {
	return []map[string]interface{}{
		{
			"result": "success",
		},
	}
}

func TestAllDatabases() bool {
	logger.Printf("Testing all database integrations...")
	
	supabase := NewMockSupabaseClient("", "")
	supabase.InsertRecord("test_table", map[string]interface{}{
		"name": "Test",
	})
	records := supabase.QueryTable("test_table")
	logger.Printf("Supabase records: %v", records)
	
	ragflow := NewMockRAGflowClient("", 0)
	results := ragflow.Search("test query", 0)
	logger.Printf("RAGflow results: %v", results)
	
	dragonfly := NewMockDragonflyClient("", 0)
	dragonfly.Set("test_key", "test_value")
	value := dragonfly.Get("test_key")
	logger.Printf("DragonflyDB value: %v", value)
	
	doris := NewMockDorisClient(nil)
	results = doris.ExecuteQuery("SELECT 1")
	logger.Printf("Doris results: %v", results)
	
	logger.Printf("All database tests completed successfully")
	return true
}

func main() {
	if TestAllDatabases() {
		os.Exit(0)
	} else {
		os.Exit(1)
	}
}
