package integrations

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"

	_ "github.com/go-sql-driver/mysql"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var dorisLogger = log.New(os.Stdout, "doris: ", log.LstdFlags)

type DorisClient struct {
	ConnectionName string
}

func NewDorisClient(connectionName string) *DorisClient {
	if connectionName == "" {
		connectionName = "default"
	}
	
	return &DorisClient{
		ConnectionName: connectionName,
	}
}

func (c *DorisClient) getConnection() (*sql.DB, error) {
	connInfo := c.GetConnectionInfo()
	
	dsn := fmt.Sprintf("%s:%s@tcp(%s:%s)/%s",
		connInfo["user"],
		"", // Password is not included in the connection info for security
		connInfo["host"],
		connInfo["port"],
		connInfo["name"],
	)
	
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database connection: %v", err)
	}
	
	return db, nil
}

func (c *DorisClient) ExecuteQuery(query string, params ...interface{}) ([]map[string]interface{}, error) {
	result, err := db.ExecuteQuery(c.ConnectionName, query, params...)
	if err != nil {
		return nil, err
	}
	
	return result, nil
}

func (c *DorisClient) ExecuteUpdate(query string, params ...interface{}) (int64, error) {
	conn, err := c.getConnection()
	if err != nil {
		return 0, err
	}
	defer conn.Close()
	
	stmt, err := conn.Prepare(query)
	if err != nil {
		return 0, fmt.Errorf("failed to prepare statement: %v", err)
	}
	defer stmt.Close()
	
	result, err := stmt.Exec(params...)
	if err != nil {
		return 0, fmt.Errorf("failed to execute statement: %v", err)
	}
	
	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return 0, fmt.Errorf("failed to get rows affected: %v", err)
	}
	
	return rowsAffected, nil
}

func (c *DorisClient) CreateTable(tableName string, columns []string, partitionBy, distributedBy string) (bool, error) {
	columnDefs := strings.Join(columns, ", ")
	query := fmt.Sprintf("CREATE TABLE IF NOT EXISTS %s (%s)", tableName, columnDefs)
	
	if partitionBy != "" {
		query += fmt.Sprintf(" PARTITION BY %s", partitionBy)
	}
	
	if distributedBy != "" {
		query += fmt.Sprintf(" DISTRIBUTED BY %s", distributedBy)
	}
	
	_, err := c.ExecuteUpdate(query)
	if err != nil {
		dorisLogger.Printf("Error creating table %s: %v\n", tableName, err)
		return false, err
	}
	
	return true, nil
}

func (c *DorisClient) DropTable(tableName string) (bool, error) {
	query := fmt.Sprintf("DROP TABLE IF EXISTS %s", tableName)
	
	_, err := c.ExecuteUpdate(query)
	if err != nil {
		dorisLogger.Printf("Error dropping table %s: %v\n", tableName, err)
		return false, err
	}
	
	return true, nil
}

func (c *DorisClient) GetTableSchema(tableName string) ([]map[string]interface{}, error) {
	query := fmt.Sprintf("DESCRIBE %s", tableName)
	
	result, err := c.ExecuteQuery(query)
	if err != nil {
		dorisLogger.Printf("Error getting schema for table %s: %v\n", tableName, err)
		return nil, err
	}
	
	return result, nil
}

func (c *DorisClient) GetTables() ([]string, error) {
	query := "SHOW TABLES"
	
	result, err := c.ExecuteQuery(query)
	if err != nil {
		dorisLogger.Printf("Error getting tables: %v\n", err)
		return nil, err
	}
	
	tables := make([]string, 0, len(result))
	for _, row := range result {
		for _, value := range row {
			if tableName, ok := value.(string); ok {
				tables = append(tables, tableName)
				break
			}
		}
	}
	
	return tables, nil
}

func (c *DorisClient) BulkLoad(tableName string, data [][]interface{}, columns []string) (int64, error) {
	if len(data) == 0 {
		return 0, nil
	}
	
	conn, err := c.getConnection()
	if err != nil {
		return 0, err
	}
	defer conn.Close()
	
	columnClause := ""
	if len(columns) > 0 {
		columnClause = fmt.Sprintf("(%s)", strings.Join(columns, ", "))
	}
	
	placeholders := make([]string, len(data[0]))
	for i := range placeholders {
		placeholders[i] = "?"
	}
	
	query := fmt.Sprintf("INSERT INTO %s %s VALUES (%s)",
		tableName,
		columnClause,
		strings.Join(placeholders, ", "),
	)
	
	stmt, err := conn.Prepare(query)
	if err != nil {
		return 0, fmt.Errorf("failed to prepare statement: %v", err)
	}
	defer stmt.Close()
	
	var totalRowsAffected int64
	for _, row := range data {
		result, err := stmt.Exec(row...)
		if err != nil {
			dorisLogger.Printf("Error bulk loading data into %s: %v\n", tableName, err)
			continue
		}
		
		rowsAffected, _ := result.RowsAffected()
		totalRowsAffected += rowsAffected
	}
	
	return totalRowsAffected, nil
}

func (c *DorisClient) GetConnectionInfo() map[string]string {
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
    'host': db_settings.get('HOST', ''),
    'port': db_settings.get('PORT', ''),
    'user': db_settings.get('USER', ''),
}

print(json.dumps(connection_info))
`, c.ConnectionName)

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		dorisLogger.Printf("Error getting connection info: %v\n", err)
		return map[string]string{}
	}
	
	var connectionInfo map[string]string
	if err := json.Unmarshal(output, &connectionInfo); err != nil {
		dorisLogger.Printf("Error unmarshaling connection info: %v\n", err)
		return map[string]string{}
	}
	
	return connectionInfo
}

func (c *DorisClient) ExecutePythonDorisMethod(methodName string, args ...interface{}) (interface{}, error) {
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

from backend.db.integrations.doris import DorisClient

client = DorisClient('%s')
method = getattr(client, '%s', None)
if not method:
    print(json.dumps({'error': 'Method not found'}))
    sys.exit(1)

args = json.loads('%s')
result = method(*args)
print(json.dumps({'result': result}))
`, c.ConnectionName, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))
	
	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("error executing Python Doris method: %v", err)
	}
	
	var result struct {
		Result interface{} `json:"result"`
		Error  string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("error unmarshaling result: %v", err)
	}
	
	if result.Error != "" {
		return nil, fmt.Errorf("Python Doris error: %s", result.Error)
	}
	
	return result.Result, nil
}

func GetDorisClient(connectionName string) *DorisClient {
	return NewDorisClient(connectionName)
}
