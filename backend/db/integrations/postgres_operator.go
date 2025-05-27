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

var postgresLogger = log.New(os.Stdout, "postgres_operator: ", log.LstdFlags)

type PostgresOperatorManager struct {
	Namespace string
}

func NewPostgresOperatorManager(namespace string) *PostgresOperatorManager {
	if namespace == "" {
		namespace = db.GetSetting("POSTGRES_OPERATOR_NAMESPACE")
		if namespace == "" {
			namespace = "default"
		}
	}

	return &PostgresOperatorManager{
		Namespace: namespace,
	}
}

func (m *PostgresOperatorManager) ApplyClusterConfig(configFile string) (bool, error) {
	cmd := exec.Command("kubectl", "apply", "-f", configFile, "-n", m.Namespace)
	output, err := cmd.CombinedOutput()
	if err != nil {
		postgresLogger.Printf("Error applying PostgreSQL cluster configuration: %v", err)
		return false, fmt.Errorf("error applying PostgreSQL cluster configuration: %v", err)
	}

	postgresLogger.Printf("Applied PostgreSQL cluster configuration: %s", string(output))
	return true, nil
}

func (m *PostgresOperatorManager) DeleteCluster(clusterName string) (bool, error) {
	cmd := exec.Command("kubectl", "delete", "postgrescluster", clusterName, "-n", m.Namespace)
	output, err := cmd.CombinedOutput()
	if err != nil {
		postgresLogger.Printf("Error deleting PostgreSQL cluster %s: %v", clusterName, err)
		return false, fmt.Errorf("error deleting PostgreSQL cluster %s: %v", clusterName, err)
	}

	postgresLogger.Printf("Deleted PostgreSQL cluster %s: %s", clusterName, string(output))
	return true, nil
}

func (m *PostgresOperatorManager) GetClusters() ([]map[string]interface{}, error) {
	cmd := exec.Command("kubectl", "get", "postgresclusters", "-n", m.Namespace, "-o", "json")
	output, err := cmd.CombinedOutput()
	if err != nil {
		postgresLogger.Printf("Error getting PostgreSQL clusters: %v", err)
		return nil, fmt.Errorf("error getting PostgreSQL clusters: %v", err)
	}

	var result struct {
		Items []map[string]interface{} `json:"items"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		postgresLogger.Printf("Error parsing PostgreSQL clusters: %v", err)
		return nil, fmt.Errorf("error parsing PostgreSQL clusters: %v", err)
	}

	return result.Items, nil
}

func (m *PostgresOperatorManager) GetCluster(clusterName string) (map[string]interface{}, error) {
	cmd := exec.Command("kubectl", "get", "postgrescluster", clusterName, "-n", m.Namespace, "-o", "json")
	output, err := cmd.CombinedOutput()
	if err != nil {
		postgresLogger.Printf("Error getting PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error getting PostgreSQL cluster %s: %v", clusterName, err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(output, &result); err != nil {
		postgresLogger.Printf("Error parsing PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error parsing PostgreSQL cluster %s: %v", clusterName, err)
	}

	return result, nil
}

func (m *PostgresOperatorManager) GetClusterStatus(clusterName string) (map[string]interface{}, error) {
	cluster, err := m.GetCluster(clusterName)
	if err != nil {
		return nil, err
	}

	status, ok := cluster["status"].(map[string]interface{})
	if !ok {
		return make(map[string]interface{}), nil
	}

	return status, nil
}

func (m *PostgresOperatorManager) GetClusterConnectionInfo(clusterName string) (map[string]interface{}, error) {
	status, err := m.GetClusterStatus(clusterName)
	if err != nil {
		return nil, err
	}

	pgbouncer, ok := status["pgbouncer"].(map[string]interface{})
	if !ok {
		return make(map[string]interface{}), nil
	}

	service, ok := pgbouncer["service"].(map[string]interface{})
	if !ok {
		return make(map[string]interface{}), nil
	}

	return service, nil
}

func (m *PostgresOperatorManager) GetClusterPods(clusterName string) ([]map[string]interface{}, error) {
	cmd := exec.Command("kubectl", "get", "pods", "-l", fmt.Sprintf("postgres-operator.crunchydata.com/cluster=%s", clusterName), "-n", m.Namespace, "-o", "json")
	output, err := cmd.CombinedOutput()
	if err != nil {
		postgresLogger.Printf("Error getting pods for PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error getting pods for PostgreSQL cluster %s: %v", clusterName, err)
	}

	var result struct {
		Items []map[string]interface{} `json:"items"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		postgresLogger.Printf("Error parsing pods for PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error parsing pods for PostgreSQL cluster %s: %v", clusterName, err)
	}

	return result.Items, nil
}

func (m *PostgresOperatorManager) GetClusterServices(clusterName string) ([]map[string]interface{}, error) {
	cmd := exec.Command("kubectl", "get", "services", "-l", fmt.Sprintf("postgres-operator.crunchydata.com/cluster=%s", clusterName), "-n", m.Namespace, "-o", "json")
	output, err := cmd.CombinedOutput()
	if err != nil {
		postgresLogger.Printf("Error getting services for PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error getting services for PostgreSQL cluster %s: %v", clusterName, err)
	}

	var result struct {
		Items []map[string]interface{} `json:"items"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		postgresLogger.Printf("Error parsing services for PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error parsing services for PostgreSQL cluster %s: %v", clusterName, err)
	}

	return result.Items, nil
}

func (m *PostgresOperatorManager) GetClusterSecrets(clusterName string) ([]map[string]interface{}, error) {
	cmd := exec.Command("kubectl", "get", "secrets", "-l", fmt.Sprintf("postgres-operator.crunchydata.com/cluster=%s", clusterName), "-n", m.Namespace, "-o", "json")
	output, err := cmd.CombinedOutput()
	if err != nil {
		postgresLogger.Printf("Error getting secrets for PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error getting secrets for PostgreSQL cluster %s: %v", clusterName, err)
	}

	var result struct {
		Items []map[string]interface{} `json:"items"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		postgresLogger.Printf("Error parsing secrets for PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error parsing secrets for PostgreSQL cluster %s: %v", clusterName, err)
	}

	return result.Items, nil
}

func (m *PostgresOperatorManager) GetOperatorStatus() (map[string]interface{}, error) {
	cmd := exec.Command("kubectl", "get", "deployment", "postgres-operator", "-n", m.Namespace, "-o", "json")
	output, err := cmd.CombinedOutput()
	if err != nil {
		postgresLogger.Printf("Error getting PostgreSQL Operator status: %v", err)
		return nil, fmt.Errorf("error getting PostgreSQL Operator status: %v", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(output, &result); err != nil {
		postgresLogger.Printf("Error parsing PostgreSQL Operator status: %v", err)
		return nil, fmt.Errorf("error parsing PostgreSQL Operator status: %v", err)
	}

	status, ok := result["status"].(map[string]interface{})
	if !ok {
		return make(map[string]interface{}), nil
	}

	return status, nil
}

func (m *PostgresOperatorManager) ExecutePythonPostgresOperatorMethod(methodName string, args ...interface{}) (interface{}, error) {
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

from backend.db.integrations.postgres_operator import PostgresOperatorManager

manager = PostgresOperatorManager("%s")
method = getattr(manager, '%s', None)
if not method:
    print(json.dumps({"error": "Method not found"}))
    sys.exit(1)

args = json.loads('%s')
result = method(*args)
print(json.dumps({"result": result}))
`, m.Namespace, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("error executing Python PostgresOperatorManager method: %v", err)
	}

	var result struct {
		Result interface{} `json:"result"`
		Error  string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("error unmarshaling result: %v", err)
	}

	if result.Error != "" {
		return nil, fmt.Errorf("Python PostgresOperatorManager error: %s", result.Error)
	}

	return result.Result, nil
}

func GetPostgresOperatorManager(namespace string) *PostgresOperatorManager {
	return NewPostgresOperatorManager(namespace)
}
