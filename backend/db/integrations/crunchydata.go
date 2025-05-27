package integrations

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	_ "github.com/lib/pq"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var crunchyLogger = log.New(os.Stdout, "crunchydata: ", log.LstdFlags)

type PostgresOperatorClient struct {
	ConnectionName string
	DBSettings map[string]string
	Namespace string
}

func NewPostgresOperatorClient(connectionName string) *PostgresOperatorClient {
	if connectionName == "" {
		connectionName = "postgres"
	}

	dbSettings := getDBSettings(connectionName)

	namespace := db.GetSetting("POSTGRES_OPERATOR_NAMESPACE")
	if namespace == "" {
		namespace = "default"
	}

	return &PostgresOperatorClient{
		ConnectionName: connectionName,
		DBSettings:     dbSettings,
		Namespace:      namespace,
	}
}

func getDBSettings(connectionName string) map[string]string {
	script := fmt.Sprintf(`
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_api.settings')
django.setup()

from django.conf import settings

db_settings = settings.DATABASES.get('%s', {})
connection_info = {
    'engine': db_settings.get('ENGINE', ''),
    'name': db_settings.get('NAME', ''),
    'host': db_settings.get('HOST', 'localhost'),
    'port': str(db_settings.get('PORT', 5432)),
    'user': db_settings.get('USER', 'postgres'),
    'password': db_settings.get('PASSWORD', ''),
}

print(json.dumps(connection_info))
`, connectionName)

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		crunchyLogger.Printf("Error getting database settings: %v", err)
		return map[string]string{}
	}

	var dbSettings map[string]string
	if err := json.Unmarshal(output, &dbSettings); err != nil {
		crunchyLogger.Printf("Error unmarshaling database settings: %v", err)
		return map[string]string{}
	}

	return dbSettings
}

func (c *PostgresOperatorClient) GetConnection() (*sql.DB, error) {
	connStr := fmt.Sprintf(
		"host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		c.DBSettings["host"],
		c.DBSettings["port"],
		c.DBSettings["user"],
		c.DBSettings["password"],
		c.DBSettings["name"],
	)

	db, err := sql.Open("postgres", connStr)
	if err != nil {
		crunchyLogger.Printf("Error connecting to database: %v", err)
		return nil, err
	}

	if err := db.Ping(); err != nil {
		crunchyLogger.Printf("Error pinging database: %v", err)
		db.Close()
		return nil, err
	}

	return db, nil
}

func (c *PostgresOperatorClient) ExecuteQuery(query string, params ...interface{}) ([]map[string]interface{}, error) {
	db, err := c.GetConnection()
	if err != nil {
		return nil, err
	}
	defer db.Close()

	rows, err := db.Query(query, params...)
	if err != nil {
		crunchyLogger.Printf("Error executing query: %v", err)
		return nil, err
	}
	defer rows.Close()

	columns, err := rows.Columns()
	if err != nil {
		crunchyLogger.Printf("Error getting column names: %v", err)
		return nil, err
	}

	result := make([]map[string]interface{}, 0)

	for rows.Next() {
		values := make([]interface{}, len(columns))
		valuePtrs := make([]interface{}, len(columns))
		for i := range columns {
			valuePtrs[i] = &values[i]
		}

		if err := rows.Scan(valuePtrs...); err != nil {
			crunchyLogger.Printf("Error scanning row: %v", err)
			return nil, err
		}

		row := make(map[string]interface{})
		for i, col := range columns {
			val := values[i]
			if b, ok := val.([]byte); ok {
				row[col] = string(b)
			} else {
				row[col] = val
			}
		}

		result = append(result, row)
	}

	if err := rows.Err(); err != nil {
		crunchyLogger.Printf("Error iterating rows: %v", err)
		return nil, err
	}

	return result, nil
}

func (c *PostgresOperatorClient) ExecuteUpdate(query string, params ...interface{}) (int64, error) {
	db, err := c.GetConnection()
	if err != nil {
		return 0, err
	}
	defer db.Close()

	result, err := db.Exec(query, params...)
	if err != nil {
		crunchyLogger.Printf("Error executing update: %v", err)
		return 0, err
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		crunchyLogger.Printf("Error getting rows affected: %v", err)
		return 0, err
	}

	return rowsAffected, nil
}

func (c *PostgresOperatorClient) GetClusters() ([]map[string]interface{}, error) {
	cmd := exec.Command("kubectl", "get", "postgresclusters", "-n", c.Namespace, "-o", "json")
	output, err := cmd.CombinedOutput()
	if err != nil {
		crunchyLogger.Printf("Error getting PostgreSQL clusters: %v", err)
		return nil, fmt.Errorf("error getting PostgreSQL clusters: %v", err)
	}

	var result struct {
		Items []map[string]interface{} `json:"items"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		crunchyLogger.Printf("Error parsing PostgreSQL clusters: %v", err)
		return nil, fmt.Errorf("error parsing PostgreSQL clusters: %v", err)
	}

	return result.Items, nil
}

func (c *PostgresOperatorClient) GetCluster(clusterName string) (map[string]interface{}, error) {
	cmd := exec.Command("kubectl", "get", "postgrescluster", clusterName, "-n", c.Namespace, "-o", "json")
	output, err := cmd.CombinedOutput()
	if err != nil {
		crunchyLogger.Printf("Error getting PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error getting PostgreSQL cluster %s: %v", clusterName, err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(output, &result); err != nil {
		crunchyLogger.Printf("Error parsing PostgreSQL cluster %s: %v", clusterName, err)
		return nil, fmt.Errorf("error parsing PostgreSQL cluster %s: %v", clusterName, err)
	}

	return result, nil
}

func (c *PostgresOperatorClient) CreateDatabase(databaseName string) (bool, error) {
	db, err := c.GetConnection()
	if err != nil {
		return false, err
	}
	defer db.Close()

	_, err = db.Exec(fmt.Sprintf("CREATE DATABASE %s", databaseName))
	if err != nil {
		crunchyLogger.Printf("Error creating database %s: %v", databaseName, err)
		return false, err
	}

	return true, nil
}

func (c *PostgresOperatorClient) DropDatabase(databaseName string) (bool, error) {
	db, err := c.GetConnection()
	if err != nil {
		return false, err
	}
	defer db.Close()

	_, err = db.Exec(fmt.Sprintf("DROP DATABASE IF EXISTS %s", databaseName))
	if err != nil {
		crunchyLogger.Printf("Error dropping database %s: %v", databaseName, err)
		return false, err
	}

	return true, nil
}

func (c *PostgresOperatorClient) CreateUser(username, password string) (bool, error) {
	db, err := c.GetConnection()
	if err != nil {
		return false, err
	}
	defer db.Close()

	_, err = db.Exec(fmt.Sprintf("CREATE USER %s WITH PASSWORD $1", username), password)
	if err != nil {
		crunchyLogger.Printf("Error creating user %s: %v", username, err)
		return false, err
	}

	return true, nil
}

func (c *PostgresOperatorClient) DropUser(username string) (bool, error) {
	db, err := c.GetConnection()
	if err != nil {
		return false, err
	}
	defer db.Close()

	_, err = db.Exec(fmt.Sprintf("DROP USER IF EXISTS %s", username))
	if err != nil {
		crunchyLogger.Printf("Error dropping user %s: %v", username, err)
		return false, err
	}

	return true, nil
}

func (c *PostgresOperatorClient) GrantPrivileges(username, databaseName, privileges string) (bool, error) {
	if privileges == "" {
		privileges = "ALL"
	}

	db, err := c.GetConnection()
	if err != nil {
		return false, err
	}
	defer db.Close()

	_, err = db.Exec(fmt.Sprintf("GRANT %s ON DATABASE %s TO %s", privileges, databaseName, username))
	if err != nil {
		crunchyLogger.Printf("Error granting privileges to %s on %s: %v", username, databaseName, err)
		return false, err
	}

	return true, nil
}

func (c *PostgresOperatorClient) GetConnectionInfo() map[string]string {
	return c.DBSettings
}

func (c *PostgresOperatorClient) ExecutePythonPostgresOperatorMethod(methodName string, args ...interface{}) (interface{}, error) {
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

from backend.db.integrations.crunchydata import PostgresOperatorClient

client = PostgresOperatorClient("%s")
method = getattr(client, '%s', None)
if not method:
    print(json.dumps({"error": "Method not found"}))
    sys.exit(1)

args = json.loads('%s')
result = method(*args)
print(json.dumps({"result": result}))
`, c.ConnectionName, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("error executing Python PostgresOperatorClient method: %v", err)
	}

	var result struct {
		Result interface{} `json:"result"`
		Error  string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("error unmarshaling result: %v", err)
	}

	if result.Error != "" {
		return nil, fmt.Errorf("Python PostgresOperatorClient error: %s", result.Error)
	}

	return result.Result, nil
}

func GetPostgresOperatorClient(connectionName string) *PostgresOperatorClient {
	return NewPostgresOperatorClient(connectionName)
}
