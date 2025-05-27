package integrations

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var ragflowLogger = log.New(os.Stdout, "kled.database.ragflow: ", log.LstdFlags)

type RAGflowManager struct {
	APIURL   string
	APIKey   string
	client   *http.Client
	hasSetup bool
}

func NewRAGflowManager(apiURL string, apiKey string) *RAGflowManager {
	ragflowConfig := db.GetSettingMap("RAGFLOW_CONFIG")

	if apiURL == "" {
		apiURL = ragflowConfig["api_url"]
		if apiURL == "" {
			apiURL = os.Getenv("RAGFLOW_API_URL")
		}
	}

	if apiKey == "" {
		apiKey = ragflowConfig["api_key"]
		if apiKey == "" {
			apiKey = os.Getenv("RAGFLOW_API_KEY")
		}
	}

	if apiURL == "" {
		ragflowLogger.Println("RAGflow API URL not provided. Using mock client.")
	}

	manager := &RAGflowManager{
		APIURL:   apiURL,
		APIKey:   apiKey,
		hasSetup: false,
	}

	manager.client = manager.createClient()
	return manager
}

func (m *RAGflowManager) createClient() *http.Client {
	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	if m.APIURL != "" {
		req, err := http.NewRequest("GET", fmt.Sprintf("%s/health", m.APIURL), nil)
		if err != nil {
			ragflowLogger.Printf("Error creating RAGflow request: %v", err)
			return client
		}

		if m.APIKey != "" {
			req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
		}
		req.Header.Set("Content-Type", "application/json")

		resp, err := client.Do(req)
		if err != nil {
			ragflowLogger.Printf("Error connecting to RAGflow API: %v", err)
			return client
		}
		defer resp.Body.Close()

		if resp.StatusCode == 200 {
			ragflowLogger.Printf("RAGflow client initialized with API URL: %s", m.APIURL)
			m.hasSetup = true
		} else {
			ragflowLogger.Printf("RAGflow API returned status code %d", resp.StatusCode)
		}
	}

	return client
}

func (m *RAGflowManager) CreateIndex(indexName string, dimension int, metric string) (bool, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning false.")
		return false, fmt.Errorf("RAGflow client not initialized")
	}

	if dimension <= 0 {
		dimension = 1536
	}

	if metric == "" {
		metric = "cosine"
	}

	payload := map[string]interface{}{
		"name":      indexName,
		"dimension": dimension,
		"metric":    metric,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		ragflowLogger.Printf("Error marshaling JSON for RAGflow: %v", err)
		return false, err
	}

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/indexes", m.APIURL), bytes.NewBuffer(jsonData))
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return false, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow index: %v", err)
		return false, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 || resp.StatusCode == 201 {
		ragflowLogger.Printf("Created RAGflow index: %s", indexName)
		return true, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return false, fmt.Errorf("error creating RAGflow index: status code %d", resp.StatusCode)
	}

	return false, fmt.Errorf("error creating RAGflow index: %v", errorResponse)
}

func (m *RAGflowManager) DeleteIndex(indexName string) (bool, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning false.")
		return false, fmt.Errorf("RAGflow client not initialized")
	}

	req, err := http.NewRequest("DELETE", fmt.Sprintf("%s/indexes/%s", m.APIURL, indexName), nil)
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return false, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error deleting RAGflow index: %v", err)
		return false, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 || resp.StatusCode == 204 {
		ragflowLogger.Printf("Deleted RAGflow index: %s", indexName)
		return true, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return false, fmt.Errorf("error deleting RAGflow index: status code %d", resp.StatusCode)
	}

	return false, fmt.Errorf("error deleting RAGflow index: %v", errorResponse)
}

func (m *RAGflowManager) ListIndexes() ([]string, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning empty list.")
		return []string{}, fmt.Errorf("RAGflow client not initialized")
	}

	req, err := http.NewRequest("GET", fmt.Sprintf("%s/indexes", m.APIURL), nil)
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return []string{}, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error listing RAGflow indexes: %v", err)
		return []string{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		var result struct {
			Indexes []string `json:"indexes"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			ragflowLogger.Printf("Error decoding RAGflow response: %v", err)
			return []string{}, err
		}
		return result.Indexes, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return []string{}, fmt.Errorf("error listing RAGflow indexes: status code %d", resp.StatusCode)
	}

	return []string{}, fmt.Errorf("error listing RAGflow indexes: %v", errorResponse)
}

func (m *RAGflowManager) AddVectors(indexName string, vectors [][]float64, ids []string, metadata []map[string]interface{}) (bool, []string, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning false.")
		return false, nil, fmt.Errorf("RAGflow client not initialized")
	}

	payload := map[string]interface{}{
		"vectors": vectors,
	}

	if ids != nil && len(ids) > 0 {
		payload["ids"] = ids
	}

	if metadata != nil && len(metadata) > 0 {
		payload["metadata"] = metadata
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		ragflowLogger.Printf("Error marshaling JSON for RAGflow: %v", err)
		return false, nil, err
	}

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/indexes/%s/vectors", m.APIURL, indexName), bytes.NewBuffer(jsonData))
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return false, nil, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error adding vectors to RAGflow index: %v", err)
		return false, nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 || resp.StatusCode == 201 {
		var result struct {
			IDs []string `json:"ids"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			ragflowLogger.Printf("Error decoding RAGflow response: %v", err)
			return true, nil, err
		}
		return true, result.IDs, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return false, nil, fmt.Errorf("error adding vectors to RAGflow index: status code %d", resp.StatusCode)
	}

	return false, nil, fmt.Errorf("error adding vectors to RAGflow index: %v", errorResponse)
}

func (m *RAGflowManager) DeleteVectors(indexName string, ids []string) (bool, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning false.")
		return false, fmt.Errorf("RAGflow client not initialized")
	}

	payload := map[string]interface{}{
		"ids": ids,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		ragflowLogger.Printf("Error marshaling JSON for RAGflow: %v", err)
		return false, err
	}

	req, err := http.NewRequest("DELETE", fmt.Sprintf("%s/indexes/%s/vectors", m.APIURL, indexName), bytes.NewBuffer(jsonData))
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return false, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error deleting vectors from RAGflow index: %v", err)
		return false, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 || resp.StatusCode == 204 {
		return true, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return false, fmt.Errorf("error deleting vectors from RAGflow index: status code %d", resp.StatusCode)
	}

	return false, fmt.Errorf("error deleting vectors from RAGflow index: %v", errorResponse)
}

func (m *RAGflowManager) Search(indexName string, queryVector []float64, topK int, filterMetadata map[string]interface{}) ([]map[string]interface{}, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning empty list.")
		return []map[string]interface{}{}, fmt.Errorf("RAGflow client not initialized")
	}

	if topK <= 0 {
		topK = 10
	}

	payload := map[string]interface{}{
		"vector": queryVector,
		"top_k":  topK,
	}

	if filterMetadata != nil {
		payload["filter"] = filterMetadata
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		ragflowLogger.Printf("Error marshaling JSON for RAGflow: %v", err)
		return []map[string]interface{}{}, err
	}

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/indexes/%s/search", m.APIURL, indexName), bytes.NewBuffer(jsonData))
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return []map[string]interface{}{}, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error searching RAGflow index: %v", err)
		return []map[string]interface{}{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		var result struct {
			Results []map[string]interface{} `json:"results"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			ragflowLogger.Printf("Error decoding RAGflow response: %v", err)
			return []map[string]interface{}{}, err
		}
		return result.Results, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return []map[string]interface{}{}, fmt.Errorf("error searching RAGflow index: status code %d", resp.StatusCode)
	}

	return []map[string]interface{}{}, fmt.Errorf("error searching RAGflow index: %v", errorResponse)
}

func (m *RAGflowManager) SemanticSearch(indexName string, queryText string, topK int, filterMetadata map[string]interface{}) ([]map[string]interface{}, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning empty list.")
		return []map[string]interface{}{}, fmt.Errorf("RAGflow client not initialized")
	}

	if topK <= 0 {
		topK = 10
	}

	payload := map[string]interface{}{
		"text":  queryText,
		"top_k": topK,
	}

	if filterMetadata != nil {
		payload["filter"] = filterMetadata
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		ragflowLogger.Printf("Error marshaling JSON for RAGflow: %v", err)
		return []map[string]interface{}{}, err
	}

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/indexes/%s/semantic-search", m.APIURL, indexName), bytes.NewBuffer(jsonData))
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return []map[string]interface{}{}, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error performing semantic search in RAGflow index: %v", err)
		return []map[string]interface{}{}, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		var result struct {
			Results []map[string]interface{} `json:"results"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			ragflowLogger.Printf("Error decoding RAGflow response: %v", err)
			return []map[string]interface{}{}, err
		}
		return result.Results, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return []map[string]interface{}{}, fmt.Errorf("error performing semantic search in RAGflow index: status code %d", resp.StatusCode)
	}

	return []map[string]interface{}{}, fmt.Errorf("error performing semantic search in RAGflow index: %v", errorResponse)
}

func (m *RAGflowManager) GetVector(indexName string, vectorID string) (map[string]interface{}, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning nil.")
		return nil, fmt.Errorf("RAGflow client not initialized")
	}

	req, err := http.NewRequest("GET", fmt.Sprintf("%s/indexes/%s/vectors/%s", m.APIURL, indexName, vectorID), nil)
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return nil, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error getting vector from RAGflow index: %v", err)
		return nil, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		var result map[string]interface{}
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			ragflowLogger.Printf("Error decoding RAGflow response: %v", err)
			return nil, err
		}
		return result, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return nil, fmt.Errorf("error getting vector from RAGflow index: status code %d", resp.StatusCode)
	}

	return nil, fmt.Errorf("error getting vector from RAGflow index: %v", errorResponse)
}

func (m *RAGflowManager) UpdateVectorMetadata(indexName string, vectorID string, metadata map[string]interface{}) (bool, error) {
	if !m.hasSetup || m.APIURL == "" {
		ragflowLogger.Println("RAGflow client not initialized. Returning false.")
		return false, fmt.Errorf("RAGflow client not initialized")
	}

	payload := map[string]interface{}{
		"metadata": metadata,
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		ragflowLogger.Printf("Error marshaling JSON for RAGflow: %v", err)
		return false, err
	}

	req, err := http.NewRequest("PATCH", fmt.Sprintf("%s/indexes/%s/vectors/%s", m.APIURL, indexName, vectorID), bytes.NewBuffer(jsonData))
	if err != nil {
		ragflowLogger.Printf("Error creating RAGflow request: %v", err)
		return false, err
	}

	if m.APIKey != "" {
		req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", m.APIKey))
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := m.client.Do(req)
	if err != nil {
		ragflowLogger.Printf("Error updating vector metadata in RAGflow index: %v", err)
		return false, err
	}
	defer resp.Body.Close()

	if resp.StatusCode == 200 {
		return true, nil
	}

	var errorResponse map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&errorResponse); err != nil {
		ragflowLogger.Printf("Error decoding RAGflow error response: %v", err)
		return false, fmt.Errorf("error updating vector metadata in RAGflow index: status code %d", resp.StatusCode)
	}

	return false, fmt.Errorf("error updating vector metadata in RAGflow index: %v", errorResponse)
}

func (m *RAGflowManager) ExecutePythonMethod(methodName string, args ...interface{}) (interface{}, error) {
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

try:
    from backend.db.integrations.ragflow import RAGflowManager
    
    manager = RAGflowManager("%s", "%s")
    method = getattr(manager, '%s', None)
    if not method:
        print(json.dumps({"success": False, "error": "Method not found"}))
        sys.exit(1)
    
    args = json.loads('%s')
    result = method(*args)
    print(json.dumps({"success": True, "result": result}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
`, m.APIURL, m.APIKey, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		ragflowLogger.Printf("Error executing Python RAGflowManager method: %v", err)
		return nil, fmt.Errorf("error executing Python RAGflowManager method: %v", err)
	}

	var result struct {
		Success bool        `json:"success"`
		Result  interface{} `json:"result"`
		Error   string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		ragflowLogger.Printf("Error unmarshaling Python RAGflowManager method result: %v", err)
		return nil, fmt.Errorf("error unmarshaling Python RAGflowManager method result: %v", err)
	}

	if !result.Success {
		ragflowLogger.Printf("Error executing Python RAGflowManager method: %s", result.Error)
		return nil, fmt.Errorf("error executing Python RAGflowManager method: %s", result.Error)
	}

	return result.Result, nil
}

var ragflowManager = NewRAGflowManager("", "")

func init() {
	db.RegisterIntegration("ragflow", "RAGflowManager")
}
