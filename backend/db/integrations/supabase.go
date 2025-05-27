package integrations

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var supabaseLogger = log.New(os.Stdout, "kled.database.supabase: ", log.LstdFlags)

type SupabaseManager struct {
	URL string
	Key string
}

func NewSupabaseManager(url, key string) *SupabaseManager {
	if url == "" {
		url = db.GetSetting("SUPABASE_URL")
		if url == "" {
			url = os.Getenv("SUPABASE_URL")
		}
	}

	if key == "" {
		key = db.GetSetting("SUPABASE_KEY")
		if key == "" {
			key = os.Getenv("SUPABASE_KEY")
		}
	}

	manager := &SupabaseManager{
		URL: url,
		Key: key,
	}

	if url != "" && key != "" {
		manager.initClient()
	} else {
		supabaseLogger.Println("Supabase URL or key not provided. Using mock client.")
	}

	return manager
}

func (m *SupabaseManager) initClient() {
	script := fmt.Sprintf(`
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_api.settings')
django.setup()

try:
    from supabase import create_client
    client = create_client("%s", "%s")
    print(json.dumps({"success": True}))
except ImportError:
    print(json.dumps({"success": False, "error": "Supabase Python SDK not installed. Install with 'pip install supabase'"}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
`, m.URL, m.Key)

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		supabaseLogger.Printf("Error initializing Supabase client: %v", err)
		return
	}

	var result struct {
		Success bool   `json:"success"`
		Error   string `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		supabaseLogger.Printf("Error unmarshaling Supabase client initialization result: %v", err)
		return
	}

	if !result.Success {
		supabaseLogger.Printf("Error initializing Supabase client: %s", result.Error)
		return
	}

	supabaseLogger.Printf("Supabase client initialized with URL: %s", m.URL)
}

func (m *SupabaseManager) ExecutePythonMethod(methodName string, args ...interface{}) (interface{}, error) {
	if m.URL == "" || m.Key == "" {
		supabaseLogger.Println("Supabase client not initialized. Returning nil.")
		return nil, nil
	}

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
    from backend.db.integrations.supabase import SupabaseManager
    
    manager = SupabaseManager("%s", "%s")
    method = getattr(manager, '%s', None)
    if not method:
        print(json.dumps({"success": False, "error": "Method not found"}))
        sys.exit(1)
    
    args = json.loads('%s')
    result = method(*args)
    print(json.dumps({"success": True, "result": result}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
`, m.URL, m.Key, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))

	cmd := exec.Command("python", "-c", script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		supabaseLogger.Printf("Error executing Python Supabase method: %v", err)
		return nil, fmt.Errorf("error executing Python Supabase method: %v", err)
	}

	var result struct {
		Success bool        `json:"success"`
		Result  interface{} `json:"result"`
		Error   string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		supabaseLogger.Printf("Error unmarshaling Python Supabase method result: %v", err)
		return nil, fmt.Errorf("error unmarshaling Python Supabase method result: %v", err)
	}

	if !result.Success {
		supabaseLogger.Printf("Error executing Python Supabase method: %s", result.Error)
		return nil, fmt.Errorf("error executing Python Supabase method: %s", result.Error)
	}

	return result.Result, nil
}

func (m *SupabaseManager) Client() interface{} {
	if m.URL == "" || m.Key == "" {
		supabaseLogger.Println("Supabase client not initialized. Returning nil.")
		return nil
	}
	return "supabase_client" // Placeholder for Python interop
}

func (m *SupabaseManager) Auth() interface{} {
	if m.URL == "" || m.Key == "" {
		supabaseLogger.Println("Supabase client not initialized. Returning nil.")
		return nil
	}
	return "supabase_auth_client" // Placeholder for Python interop
}

func (m *SupabaseManager) Storage() interface{} {
	if m.URL == "" || m.Key == "" {
		supabaseLogger.Println("Supabase client not initialized. Returning nil.")
		return nil
	}
	return "supabase_storage_client" // Placeholder for Python interop
}

func (m *SupabaseManager) Functions() interface{} {
	if m.URL == "" || m.Key == "" {
		supabaseLogger.Println("Supabase client not initialized. Returning nil.")
		return nil
	}
	return "supabase_functions_client" // Placeholder for Python interop
}

func (m *SupabaseManager) QueryTable(tableName string, queryParams map[string]interface{}) ([]map[string]interface{}, error) {
	result, err := m.ExecutePythonMethod("query_table", tableName, queryParams)
	if err != nil {
		return nil, err
	}
	
	if result == nil {
		return []map[string]interface{}{}, nil
	}
	
	resultJSON, err := json.Marshal(result)
	if err != nil {
		return nil, fmt.Errorf("error marshaling result: %v", err)
	}
	
	var records []map[string]interface{}
	if err := json.Unmarshal(resultJSON, &records); err != nil {
		return nil, fmt.Errorf("error unmarshaling records: %v", err)
	}
	
	return records, nil
}

func (m *SupabaseManager) InsertRecord(tableName string, record map[string]interface{}) (map[string]interface{}, error) {
	result, err := m.ExecutePythonMethod("insert_record", tableName, record)
	if err != nil {
		return nil, err
	}
	
	if result == nil {
		return map[string]interface{}{}, nil
	}
	
	resultJSON, err := json.Marshal(result)
	if err != nil {
		return nil, fmt.Errorf("error marshaling result: %v", err)
	}
	
	var recordResult map[string]interface{}
	if err := json.Unmarshal(resultJSON, &recordResult); err != nil {
		return nil, fmt.Errorf("error unmarshaling record: %v", err)
	}
	
	return recordResult, nil
}

func (m *SupabaseManager) UpdateRecord(tableName string, recordID string, record map[string]interface{}) (map[string]interface{}, error) {
	result, err := m.ExecutePythonMethod("update_record", tableName, recordID, record)
	if err != nil {
		return nil, err
	}
	
	if result == nil {
		return map[string]interface{}{}, nil
	}
	
	resultJSON, err := json.Marshal(result)
	if err != nil {
		return nil, fmt.Errorf("error marshaling result: %v", err)
	}
	
	var recordResult map[string]interface{}
	if err := json.Unmarshal(resultJSON, &recordResult); err != nil {
		return nil, fmt.Errorf("error unmarshaling record: %v", err)
	}
	
	return recordResult, nil
}

func (m *SupabaseManager) DeleteRecord(tableName string, recordID string) (bool, error) {
	result, err := m.ExecutePythonMethod("delete_record", tableName, recordID)
	if err != nil {
		return false, err
	}
	
	success, ok := result.(bool)
	if !ok {
		return false, fmt.Errorf("unexpected result type: %T", result)
	}
	
	return success, nil
}

func (m *SupabaseManager) ExecuteRPC(functionName string, params map[string]interface{}) (interface{}, error) {
	return m.ExecutePythonMethod("execute_rpc", functionName, params)
}

func (m *SupabaseManager) AuthenticateUser(email, password string) (bool, map[string]interface{}, error) {
	result, err := m.ExecutePythonMethod("authenticate_user", email, password)
	if err != nil {
		return false, nil, err
	}
	
	if result == nil {
		return false, nil, nil
	}
	
	resultJSON, err := json.Marshal(result)
	if err != nil {
		return false, nil, fmt.Errorf("error marshaling result: %v", err)
	}
	
	var authResult []interface{}
	if err := json.Unmarshal(resultJSON, &authResult); err != nil {
		return false, nil, fmt.Errorf("error unmarshaling auth result: %v", err)
	}
	
	if len(authResult) != 2 {
		return false, nil, fmt.Errorf("unexpected auth result length: %d", len(authResult))
	}
	
	success, ok := authResult[0].(bool)
	if !ok {
		return false, nil, fmt.Errorf("unexpected success type: %T", authResult[0])
	}
	
	if !success || authResult[1] == nil {
		return false, nil, nil
	}
	
	userJSON, err := json.Marshal(authResult[1])
	if err != nil {
		return true, nil, fmt.Errorf("error marshaling user data: %v", err)
	}
	
	var userData map[string]interface{}
	if err := json.Unmarshal(userJSON, &userData); err != nil {
		return true, nil, fmt.Errorf("error unmarshaling user data: %v", err)
	}
	
	return true, userData, nil
}

func (m *SupabaseManager) CreateUser(email, password string, userData map[string]interface{}) (bool, map[string]interface{}, error) {
	result, err := m.ExecutePythonMethod("create_user", email, password, userData)
	if err != nil {
		return false, nil, err
	}
	
	if result == nil {
		return false, nil, nil
	}
	
	resultJSON, err := json.Marshal(result)
	if err != nil {
		return false, nil, fmt.Errorf("error marshaling result: %v", err)
	}
	
	var createResult []interface{}
	if err := json.Unmarshal(resultJSON, &createResult); err != nil {
		return false, nil, fmt.Errorf("error unmarshaling create result: %v", err)
	}
	
	if len(createResult) != 2 {
		return false, nil, fmt.Errorf("unexpected create result length: %d", len(createResult))
	}
	
	success, ok := createResult[0].(bool)
	if !ok {
		return false, nil, fmt.Errorf("unexpected success type: %T", createResult[0])
	}
	
	if !success || createResult[1] == nil {
		return false, nil, nil
	}
	
	userJSON, err := json.Marshal(createResult[1])
	if err != nil {
		return true, nil, fmt.Errorf("error marshaling user data: %v", err)
	}
	
	var user map[string]interface{}
	if err := json.Unmarshal(userJSON, &user); err != nil {
		return true, nil, fmt.Errorf("error unmarshaling user data: %v", err)
	}
	
	return true, user, nil
}

func (m *SupabaseManager) UploadFile(bucket, path string, fileData []byte, contentType string) (bool, string, error) {
	tempFile, err := os.CreateTemp("", "supabase_upload_*")
	if err != nil {
		return false, "", fmt.Errorf("error creating temporary file: %v", err)
	}
	defer os.Remove(tempFile.Name())
	defer tempFile.Close()

	if _, err := tempFile.Write(fileData); err != nil {
		return false, "", fmt.Errorf("error writing to temporary file: %v", err)
	}

	script := fmt.Sprintf(`
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_api.settings')
django.setup()

try:
    from backend.db.integrations.supabase import SupabaseManager
    
    manager = SupabaseManager("%s", "%s")
    with open("%s", "rb") as f:
        file_data = f.read()
        success, file_url = manager.upload_file("%s", "%s", file_data, "%s")
    print(json.dumps({"success": True, "result": success, "file_url": file_url}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
`, m.URL, m.Key, tempFile.Name(), bucket, path, contentType)

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return false, "", fmt.Errorf("error uploading file: %v", err)
	}

	var result struct {
		Success bool   `json:"success"`
		Result  bool   `json:"result"`
		FileURL string `json:"file_url"`
		Error   string `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return false, "", fmt.Errorf("error unmarshaling result: %v", err)
	}

	if !result.Success {
		return false, "", fmt.Errorf("error from Python: %s", result.Error)
	}

	return result.Result, result.FileURL, nil
}

func (m *SupabaseManager) DownloadFile(bucket, path string) (bool, []byte, error) {
	result, err := m.ExecutePythonMethod("download_file", bucket, path)
	if err != nil {
		return false, nil, err
	}
	
	if result == nil {
		return false, nil, nil
	}
	
	resultJSON, err := json.Marshal(result)
	if err != nil {
		return false, nil, fmt.Errorf("error marshaling result: %v", err)
	}
	
	var downloadResult []interface{}
	if err := json.Unmarshal(resultJSON, &downloadResult); err != nil {
		return false, nil, fmt.Errorf("error unmarshaling download result: %v", err)
	}
	
	if len(downloadResult) != 2 {
		return false, nil, fmt.Errorf("unexpected download result length: %d", len(downloadResult))
	}
	
	success, ok := downloadResult[0].(bool)
	if !ok {
		return false, nil, fmt.Errorf("unexpected success type: %T", downloadResult[0])
	}
	
	if !success || downloadResult[1] == nil {
		return false, nil, nil
	}
	
	fileDataStr, ok := downloadResult[1].(string)
	if !ok {
		return true, nil, fmt.Errorf("unexpected file data type: %T", downloadResult[1])
	}
	
	return true, []byte(fileDataStr), nil
}

func (m *SupabaseManager) InvokeFunction(functionName string, payload map[string]interface{}, headers map[string]string) (bool, interface{}, error) {
	result, err := m.ExecutePythonMethod("invoke_function", functionName, payload, headers)
	if err != nil {
		return false, nil, err
	}
	
	if result == nil {
		return false, nil, nil
	}
	
	resultJSON, err := json.Marshal(result)
	if err != nil {
		return false, nil, fmt.Errorf("error marshaling result: %v", err)
	}
	
	var invokeResult []interface{}
	if err := json.Unmarshal(resultJSON, &invokeResult); err != nil {
		return false, nil, fmt.Errorf("error unmarshaling invoke result: %v", err)
	}
	
	if len(invokeResult) != 2 {
		return false, nil, fmt.Errorf("unexpected invoke result length: %d", len(invokeResult))
	}
	
	success, ok := invokeResult[0].(bool)
	if !ok {
		return false, nil, fmt.Errorf("unexpected success type: %T", invokeResult[0])
	}
	
	return success, invokeResult[1], nil
}

var supabaseManager = NewSupabaseManager("", "")
