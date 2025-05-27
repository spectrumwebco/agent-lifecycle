package integrations

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var dragonflyLogger = log.New(os.Stdout, "kled.database.dragonfly: ", log.LstdFlags)

type DragonflyManager struct {
	Host     string
	Port     int
	DB       int
	Password string
	UseSSL   bool
	client   *redis.Client
}

func NewDragonflyManager(host string, port int, db int, password string, useSSL bool) *DragonflyManager {
	redisConfig := db.GetSettingMap("DRAGONFLY_CONFIG")

	if host == "" {
		host = redisConfig["host"]
		if host == "" {
			host = "localhost"
		}
	}

	if port == 0 {
		portStr := redisConfig["port"]
		if portStr != "" {
			var err error
			port, err = strconv.Atoi(portStr)
			if err != nil {
				port = 6379
			}
		} else {
			port = 6379
		}
	}

	if db < 0 {
		dbStr := redisConfig["db"]
		if dbStr != "" {
			var err error
			db, err = strconv.Atoi(dbStr)
			if err != nil {
				db = 0
			}
		} else {
			db = 0
		}
	}

	if password == "" {
		password = redisConfig["password"]
	}

	if !useSSL {
		useSSLStr := redisConfig["use_ssl"]
		if useSSLStr != "" {
			useSSL = useSSLStr == "True" || useSSLStr == "true" || useSSLStr == "1"
		}
	}

	manager := &DragonflyManager{
		Host:     host,
		Port:     port,
		DB:       db,
		Password: password,
		UseSSL:   useSSL,
	}

	manager.client = manager.createClient()
	return manager
}

func (m *DragonflyManager) createClient() *redis.Client {
	client := redis.NewClient(&redis.Options{
		Addr:     fmt.Sprintf("%s:%d", m.Host, m.Port),
		Password: m.Password,
		DB:       m.DB,
		TLSConfig: func() interface{} {
			if m.UseSSL {
				return &tls.Config{
					MinVersion: tls.VersionTLS12,
				}
			}
			return nil
		}(),
	})

	ctx := context.Background()
	_, err := client.Ping(ctx).Result()
	if err != nil {
		dragonflyLogger.Printf("Error creating DragonflyDB client: %v", err)
		return nil
	}

	dragonflyLogger.Printf("DragonflyDB client initialized with host: %s, port: %d", m.Host, m.Port)
	return client
}

func (m *DragonflyManager) Client() *redis.Client {
	return m.client
}

func (m *DragonflyManager) Get(key string) (string, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning empty string.")
		return "", fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	val, err := m.client.Get(ctx, key).Result()
	if err == redis.Nil {
		return "", nil
	} else if err != nil {
		dragonflyLogger.Printf("Error getting value from DragonflyDB: %v", err)
		return "", err
	}

	return val, nil
}

func (m *DragonflyManager) Set(key string, value string, ex int) (bool, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning false.")
		return false, fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	var expiration time.Duration
	if ex > 0 {
		expiration = time.Duration(ex) * time.Second
	}

	_, err := m.client.Set(ctx, key, value, expiration).Result()
	if err != nil {
		dragonflyLogger.Printf("Error setting value in DragonflyDB: %v", err)
		return false, err
	}

	return true, nil
}

func (m *DragonflyManager) Delete(key string) (bool, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning false.")
		return false, fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	result, err := m.client.Del(ctx, key).Result()
	if err != nil {
		dragonflyLogger.Printf("Error deleting key from DragonflyDB: %v", err)
		return false, err
	}

	return result > 0, nil
}

func (m *DragonflyManager) Exists(key string) (bool, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning false.")
		return false, fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	result, err := m.client.Exists(ctx, key).Result()
	if err != nil {
		dragonflyLogger.Printf("Error checking if key exists in DragonflyDB: %v", err)
		return false, err
	}

	return result > 0, nil
}

func (m *DragonflyManager) Expire(key string, seconds int) (bool, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning false.")
		return false, fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	result, err := m.client.Expire(ctx, key, time.Duration(seconds)*time.Second).Result()
	if err != nil {
		dragonflyLogger.Printf("Error setting expiration for key in DragonflyDB: %v", err)
		return false, err
	}

	return result, nil
}

func (m *DragonflyManager) GetJSON(key string) (map[string]interface{}, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning nil.")
		return nil, fmt.Errorf("DragonflyDB client not initialized")
	}

	value, err := m.Get(key)
	if err != nil {
		return nil, err
	}

	if value == "" {
		return nil, nil
	}

	var result map[string]interface{}
	if err := json.Unmarshal([]byte(value), &result); err != nil {
		dragonflyLogger.Printf("Error decoding JSON from DragonflyDB: %v", err)
		return nil, err
	}

	return result, nil
}

func (m *DragonflyManager) SetJSON(key string, value map[string]interface{}, ex int) (bool, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning false.")
		return false, fmt.Errorf("DragonflyDB client not initialized")
	}

	jsonValue, err := json.Marshal(value)
	if err != nil {
		dragonflyLogger.Printf("Error encoding JSON for DragonflyDB: %v", err)
		return false, err
	}

	return m.Set(key, string(jsonValue), ex)
}

func (m *DragonflyManager) HGet(name string, key string) (string, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning empty string.")
		return "", fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	val, err := m.client.HGet(ctx, name, key).Result()
	if err == redis.Nil {
		return "", nil
	} else if err != nil {
		dragonflyLogger.Printf("Error getting value from hash in DragonflyDB: %v", err)
		return "", err
	}

	return val, nil
}

func (m *DragonflyManager) HSet(name string, key string, value string) (bool, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning false.")
		return false, fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	_, err := m.client.HSet(ctx, name, key, value).Result()
	if err != nil {
		dragonflyLogger.Printf("Error setting value in hash in DragonflyDB: %v", err)
		return false, err
	}

	return true, nil
}

func (m *DragonflyManager) HGetAll(name string) (map[string]string, error) {
	if m.client == nil {
		dragonflyLogger.Println("DragonflyDB client not initialized. Returning empty map.")
		return map[string]string{}, fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	result, err := m.client.HGetAll(ctx, name).Result()
	if err != nil {
		dragonflyLogger.Printf("Error getting all key-value pairs from hash in DragonflyDB: %v", err)
		return map[string]string{}, err
	}

	return result, nil
}

func (m *DragonflyManager) MemcachedGet(key string) (string, error) {
	return m.Get(key)
}

func (m *DragonflyManager) MemcachedSet(key string, value string, ex int) (bool, error) {
	return m.Set(key, value, ex)
}

func (m *DragonflyManager) CacheGet(key string) (interface{}, error) {
	value, err := m.GetJSON(key)
	if err != nil {
		return nil, err
	}

	if value == nil {
		return nil, nil
	}

	expiresAt, ok := value["expires_at"].(float64)
	if ok && expiresAt > 0 {
		now := float64(time.Now().Unix())
		if now > expiresAt {
			m.Delete(key)
			return nil, nil
		}
	}

	return value["value"], nil
}

func (m *DragonflyManager) CacheSet(key string, value interface{}, timeout int) (bool, error) {
	var expiresAt float64
	if timeout > 0 {
		expiresAt = float64(time.Now().Unix() + int64(timeout))
	}

	data := map[string]interface{}{
		"value":      value,
		"expires_at": expiresAt,
	}

	return m.SetJSON(key, data, timeout)
}

func (m *DragonflyManager) ExecutePythonMethod(methodName string, args ...interface{}) (interface{}, error) {
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
    from backend.db.integrations.dragonfly import DragonflyManager
    
    manager = DragonflyManager("%s", %d, %d, "%s", %v)
    method = getattr(manager, '%s', None)
    if not method:
        print(json.dumps({"success": False, "error": "Method not found"}))
        sys.exit(1)
    
    args = json.loads('%s')
    result = method(*args)
    print(json.dumps({"success": True, "result": result}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
`, m.Host, m.Port, m.DB, m.Password, m.UseSSL, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		dragonflyLogger.Printf("Error executing Python DragonflyManager method: %v", err)
		return nil, fmt.Errorf("error executing Python DragonflyManager method: %v", err)
	}

	var result struct {
		Success bool        `json:"success"`
		Result  interface{} `json:"result"`
		Error   string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		dragonflyLogger.Printf("Error unmarshaling Python DragonflyManager method result: %v", err)
		return nil, fmt.Errorf("error unmarshaling Python DragonflyManager method result: %v", err)
	}

	if !result.Success {
		dragonflyLogger.Printf("Error executing Python DragonflyManager method: %s", result.Error)
		return nil, fmt.Errorf("error executing Python DragonflyManager method: %s", result.Error)
	}

	return result.Result, nil
}

type DragonflyCache struct {
	Manager *DragonflyManager
	Options map[string]string
	Server  string
}

func NewDragonflyCache(server string, params map[string]string) *DragonflyCache {
	parts := strings.Split(server, ":")
	if len(parts) != 2 {
		dragonflyLogger.Printf("Invalid server address: %s", server)
		return nil
	}

	host := parts[0]
	port, err := strconv.Atoi(parts[1])
	if err != nil {
		dragonflyLogger.Printf("Invalid port: %s", parts[1])
		return nil
	}

	db := 0
	if dbStr, ok := params["db"]; ok {
		db, _ = strconv.Atoi(dbStr)
	}

	password := ""
	if pwd, ok := params["password"]; ok {
		password = pwd
	}

	useSSL := false
	if sslStr, ok := params["use_ssl"]; ok {
		useSSL = sslStr == "True" || sslStr == "true" || sslStr == "1"
	}

	manager := NewDragonflyManager(host, port, db, password, useSSL)

	return &DragonflyCache{
		Manager: manager,
		Options: params,
		Server:  server,
	}
}

func (c *DragonflyCache) Add(key string, value interface{}, timeout int) (bool, error) {
	exists, err := c.Manager.Exists(key)
	if err != nil {
		return false, err
	}

	if exists {
		return false, nil
	}

	return c.Manager.CacheSet(key, value, timeout)
}

func (c *DragonflyCache) Get(key string, defaultValue interface{}) (interface{}, error) {
	value, err := c.Manager.CacheGet(key)
	if err != nil {
		return defaultValue, err
	}

	if value == nil {
		return defaultValue, nil
	}

	return value, nil
}

func (c *DragonflyCache) Set(key string, value interface{}, timeout int) (bool, error) {
	return c.Manager.CacheSet(key, value, timeout)
}

func (c *DragonflyCache) Delete(key string) (bool, error) {
	return c.Manager.Delete(key)
}

func (c *DragonflyCache) HasKey(key string) (bool, error) {
	return c.Manager.Exists(key)
}

func (c *DragonflyCache) Clear() (bool, error) {
	if c.Manager.client == nil {
		return false, fmt.Errorf("DragonflyDB client not initialized")
	}

	ctx := context.Background()
	_, err := c.Manager.client.FlushDB(ctx).Result()
	if err != nil {
		dragonflyLogger.Printf("Error clearing DragonflyDB cache: %v", err)
		return false, err
	}

	return true, nil
}

func (c *DragonflyCache) ExecutePythonCacheMethod(methodName string, args ...interface{}) (interface{}, error) {
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
    from backend.db.integrations.dragonfly import DragonflyCache
    
    params = %s
    cache = DragonflyCache("%s", params)
    method = getattr(cache, '%s', None)
    if not method:
        print(json.dumps({"success": False, "error": "Method not found"}))
        sys.exit(1)
    
    args = json.loads('%s')
    result = method(*args)
    print(json.dumps({"success": True, "result": result}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}))
`, c.Options, c.Server, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		dragonflyLogger.Printf("Error executing Python DragonflyCache method: %v", err)
		return nil, fmt.Errorf("error executing Python DragonflyCache method: %v", err)
	}

	var result struct {
		Success bool        `json:"success"`
		Result  interface{} `json:"result"`
		Error   string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		dragonflyLogger.Printf("Error unmarshaling Python DragonflyCache method result: %v", err)
		return nil, fmt.Errorf("error unmarshaling Python DragonflyCache method result: %v", err)
	}

	if !result.Success {
		dragonflyLogger.Printf("Error executing Python DragonflyCache method: %s", result.Error)
		return nil, fmt.Errorf("error executing Python DragonflyCache method: %s", result.Error)
	}

	return result.Result, nil
}

var dragonflyManager = NewDragonflyManager("", 0, -1, "", false)
