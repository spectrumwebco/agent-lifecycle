package tests

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var logger *log.Logger

func init() {
	logger = log.New(os.Stdout, "", log.LstdFlags)
	logger.SetPrefix(time.Now().Format("2006-01-02 15:04:05") + " - database-test - INFO - ")
}

func TestSupabase() bool {
	logger.Println("Testing Supabase integration...")

	script := `
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database-test")

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from apps.python_agent.integrations.mock_db import MockSupabaseClient
    
    client = MockSupabaseClient(url="mock://supabase", key="mock-key")
    
    logger.info("Testing query operations...")
    records = client.query_table('test_table')
    logger.info(f"Query result: {records}")
    
    logger.info("Testing insert operations...")
    record = client.insert_record('test_table', {'name': 'Test Record'})
    logger.info(f"Insert result: {record}")
    
    logger.info("Supabase integration test passed")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"Supabase integration test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("Supabase integration test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("Supabase integration test failed: %s", outputStr)
		return false
	}

	logger.Printf("Supabase test output: %s", outputStr)
	return true
}

func TestRAGflow() bool {
	logger.Println("Testing RAGflow integration...")

	script := `
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database-test")

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from apps.python_agent.integrations.mock_db import MockRAGflowClient
    
    client = MockRAGflowClient(host="localhost", port=8000, api_key="mock-key")
    
    logger.info("Testing search functionality...")
    results = client.search("test query")
    logger.info(f"Search result: {results}")
    
    logger.info("Testing semantic search functionality...")
    results = client.semantic_search("test query")
    logger.info(f"Semantic search result: {results}")
    
    logger.info("RAGflow integration test passed")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"RAGflow integration test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("RAGflow integration test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("RAGflow integration test failed: %s", outputStr)
		return false
	}

	logger.Printf("RAGflow test output: %s", outputStr)
	return true
}

func TestDragonfly() bool {
	logger.Println("Testing DragonflyDB integration...")

	script := `
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database-test")

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from apps.python_agent.integrations.mock_db import MockDragonflyClient
    
    client = MockDragonflyClient(host="localhost", port=6379, mock=True)
    
    logger.info("Testing key-value operations...")
    client.set("test_key", "test_value")
    value = client.get("test_key")
    logger.info(f"Get result: {value}")
    
    logger.info("Testing memcached operations...")
    client.memcached_set("test_memcached_key", "test_memcached_value")
    value = client.memcached_get("test_memcached_key")
    logger.info(f"Memcached get result: {value}")
    
    logger.info("DragonflyDB integration test passed")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"DragonflyDB integration test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("DragonflyDB integration test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("DragonflyDB integration test failed: %s", outputStr)
		return false
	}

	logger.Printf("DragonflyDB test output: %s", outputStr)
	return true
}

func TestRocketMQ() bool {
	logger.Println("Testing RocketMQ integration...")

	script := `
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database-test")

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from apps.python_agent.integrations.mock_db import MockRocketMQClient
    
    client = MockRocketMQClient(host="localhost", port=9876, mock=True)
    
    logger.info("Testing message production and consumption...")
    message_id = client.send_message("test_topic", {"test": "message"})
    logger.info(f"Message ID: {message_id}")
    
    message = client.consume_message("test_topic")
    logger.info(f"Consumed message: {message}")
    
    logger.info("Testing state management...")
    client.update_state("test_state", {"status": "testing"})
    state = client.get_state("test_state")
    logger.info(f"State: {state}")
    
    logger.info("RocketMQ integration test passed")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"RocketMQ integration test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("RocketMQ integration test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("RocketMQ integration test failed: %s", outputStr)
		return false
	}

	logger.Printf("RocketMQ test output: %s", outputStr)
	return true
}

func TestDoris() bool {
	logger.Println("Testing Apache Doris integration...")

	script := `
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database-test")

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from apps.python_agent.integrations.mock_db import MockDorisClient
    
    client = MockDorisClient(connection_params={
        "host": "localhost",
        "port": 9030,
        "user": "root",
        "password": ""
    }, mock=True)
    
    logger.info("Testing query execution...")
    results = client.execute_query("SELECT 1")
    logger.info(f"Query result: {results}")
    
    logger.info("Testing table operations...")
    client.create_table("test_table", {
        "id": "INT",
        "name": "VARCHAR(100)",
        "created_at": "DATETIME"
    })
    
    client.insert_data("test_table", [
        {"id": 1, "name": "Test 1", "created_at": "2023-01-01 00:00:00"},
        {"id": 2, "name": "Test 2", "created_at": "2023-01-02 00:00:00"}
    ])
    
    results = client.execute_query("SELECT * FROM test_table")
    logger.info(f"Table data: {results}")
    
    logger.info("Apache Doris integration test passed")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"Apache Doris integration test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("Apache Doris integration test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("Apache Doris integration test failed: %s", outputStr)
		return false
	}

	logger.Printf("Apache Doris test output: %s", outputStr)
	return true
}

func TestPostgres() bool {
	logger.Println("Testing PostgreSQL integration...")

	script := `
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database-test")

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from apps.python_agent.integrations.mock_db import MockPostgresClient
    
    client = MockPostgresClient(host="localhost", port=5432, user="postgres", password="", mock=True)
    
    logger.info("Testing query execution...")
    results = client.execute_query("SELECT 1")
    logger.info(f"Query result: {results}")
    
    logger.info("Testing table operations...")
    client.create_table("test_table", {
        "id": "SERIAL PRIMARY KEY",
        "name": "VARCHAR(100)",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    
    client.insert_data("test_table", [
        {"name": "Test 1"},
        {"name": "Test 2"}
    ])
    
    results = client.execute_query("SELECT * FROM test_table")
    logger.info(f"Table data: {results}")
    
    logger.info("PostgreSQL integration test passed")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"PostgreSQL integration test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("PostgreSQL integration test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("PostgreSQL integration test failed: %s", outputStr)
		return false
	}

	logger.Printf("PostgreSQL test output: %s", outputStr)
	return true
}

func TestKafka() bool {
	logger.Println("Testing Kafka integration...")

	script := `
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("database-test")

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from apps.python_agent.integrations.mock_db import MockKafkaClient
    
    client = MockKafkaClient(bootstrap_servers="localhost:9092", mock=True)
    
    logger.info("Testing message production and consumption...")
    client.produce_message("test_topic", {"test": "message"})
    
    message = client.consume_message("test_topic")
    logger.info(f"Consumed message: {message}")
    
    logger.info("Kafka integration test passed")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"Kafka integration test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("Kafka integration test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("Kafka integration test failed: %s", outputStr)
		return false
	}

	logger.Printf("Kafka test output: %s", outputStr)
	return true
}

func RunMockDatabaseTests() int {
	logger.Println("Starting database integration tests")

	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		logger.Printf("Error getting current directory: %v", err)
		return 1
	}
	err = os.Chdir(dir)
	if err != nil {
		logger.Printf("Error changing directory: %v", err)
		return 1
	}

	success := true

	if !TestSupabase() {
		success = false
	}

	if !TestRAGflow() {
		success = false
	}

	if !TestDragonfly() {
		success = false
	}

	if !TestRocketMQ() {
		success = false
	}

	if !TestDoris() {
		success = false
	}

	if !TestPostgres() {
		success = false
	}

	if !TestKafka() {
		success = false
	}

	if success {
		logger.Println("All database integration tests passed")
		return 0
	} else {
		logger.Println("Some database integration tests failed")
		return 1
	}
}

func main() {
	os.Exit(RunMockDatabaseTests())
}
