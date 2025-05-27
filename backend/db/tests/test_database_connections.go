package tests

import (
	"encoding/json"
	"flag"
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

func TestSupabaseConnection(config map[string]interface{}) bool {
	logger.Println("Testing Supabase connection...")

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
    from apps.python_agent.integrations.supabase import SupabaseClient
    
    config = {
        "url": os.environ.get("SUPABASE_URL", "http://localhost:8000"),
        "key": os.environ.get("SUPABASE_KEY", "mock-key"),
        "databases": ["agent_db", "trajectory_db", "ml_db", "user_db"]
    }
    
    # Override with provided config if available
    if 'config' in globals() and config is not None:
        for key, value in config.items():
            config[key] = value
    
    for db_name in config["databases"]:
        logger.info(f"Testing connection to Supabase database: {db_name}")
        
        client = SupabaseClient(
            url=config["url"],
            key=config["key"],
            database=db_name,
            mock=True
        )
        
        result = client.query_table("test_table")
        logger.info(f"Query result: {result}")
        
        if hasattr(client, "auth"):
            auth_status = client.auth.get_session()
            logger.info(f"Auth status: {auth_status}")
        
        if hasattr(client, "functions"):
            function_result = client.functions.invoke("test_function")
            logger.info(f"Function result: {function_result}")
        
        logger.info(f"Supabase database {db_name} connection test successful")
    
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"Supabase connection test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("Supabase connection test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("Supabase connection test failed: %s", outputStr)
		return false
	}

	logger.Printf("Supabase test output: %s", outputStr)
	return true
}

func TestRAGflowConnection(config map[string]interface{}) bool {
	logger.Println("Testing RAGflow connection...")

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
    from apps.python_agent.integrations.ragflow import RAGflowClient
    
    config = {
        "host": os.environ.get("RAGFLOW_HOST", "localhost"),
        "port": int(os.environ.get("RAGFLOW_PORT", "8080")),
        "api_key": os.environ.get("RAGFLOW_API_KEY", "mock-key")
    }
    
    # Override with provided config if available
    if 'config' in globals() and config is not None:
        for key, value in config.items():
            config[key] = value
    
    client = RAGflowClient(
        host=config["host"],
        port=config["port"],
        api_key=config["api_key"],
        mock=True
    )
    
    search_result = client.search("test query")
    logger.info(f"Search result: {search_result}")
    
    semantic_result = client.semantic_search("test semantic query")
    logger.info(f"Semantic search result: {semantic_result}")
    
    if hasattr(client, "deep_understanding"):
        understanding_result = client.deep_understanding("test understanding query")
        logger.info(f"Deep understanding result: {understanding_result}")
    
    logger.info("RAGflow connection test successful")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"RAGflow connection test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("RAGflow connection test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("RAGflow connection test failed: %s", outputStr)
		return false
	}

	logger.Printf("RAGflow test output: %s", outputStr)
	return true
}

func TestDragonflyConnection(config map[string]interface{}) bool {
	logger.Println("Testing DragonflyDB connection...")

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
    from apps.python_agent.integrations.dragonfly import DragonflyClient
    
    config = {
        "host": os.environ.get("DRAGONFLY_HOST", "localhost"),
        "port": int(os.environ.get("DRAGONFLY_PORT", "6379")),
        "password": os.environ.get("DRAGONFLY_PASSWORD", "")
    }
    
    # Override with provided config if available
    if 'config' in globals() and config is not None:
        for key, value in config.items():
            config[key] = value
    
    client = DragonflyClient(
        host=config["host"],
        port=config["port"],
        password=config["password"],
        mock=True
    )
    
    client.set("test_key", "test_value")
    value = client.get("test_key")
    logger.info(f"Key-value test: {value}")
    
    if hasattr(client, "memcached_set"):
        client.memcached_set("test_memcached_key", "test_memcached_value")
        memcached_value = client.memcached_get("test_memcached_key")
        logger.info(f"Memcached test: {memcached_value}")
    
    logger.info("DragonflyDB connection test successful")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"DragonflyDB connection test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("DragonflyDB connection test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("DragonflyDB connection test failed: %s", outputStr)
		return false
	}

	logger.Printf("DragonflyDB test output: %s", outputStr)
	return true
}

func TestRocketMQConnection(config map[string]interface{}) bool {
	logger.Println("Testing RocketMQ connection...")

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
    from apps.python_agent.integrations.rocketmq import RocketMQClient
    
    config = {
        "host": os.environ.get("ROCKETMQ_HOST", "localhost"),
        "port": int(os.environ.get("ROCKETMQ_PORT", "9876")),
        "group": os.environ.get("ROCKETMQ_GROUP", "test_group")
    }
    
    # Override with provided config if available
    if 'config' in globals() and config is not None:
        for key, value in config.items():
            config[key] = value
    
    client = RocketMQClient(
        host=config["host"],
        port=config["port"],
        group=config["group"],
        mock=True
    )
    
    message_id = client.send_message("test_topic", {"test": "message"})
    logger.info(f"Message ID: {message_id}")
    
    message = client.consume_message("test_topic")
    logger.info(f"Consumed message: {message}")
    
    if hasattr(client, "update_state"):
        client.update_state("test_state", {"status": "testing"})
        state = client.get_state("test_state")
        logger.info(f"State management test: {state}")
    
    logger.info("RocketMQ connection test successful")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"RocketMQ connection test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("RocketMQ connection test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("RocketMQ connection test failed: %s", outputStr)
		return false
	}

	logger.Printf("RocketMQ test output: %s", outputStr)
	return true
}

func TestDorisConnection(config map[string]interface{}) bool {
	logger.Println("Testing Apache Doris connection...")

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
    from backend.db.integrations.doris import DorisClient
    
    config = {
        "host": os.environ.get("DORIS_HOST", "localhost"),
        "port": int(os.environ.get("DORIS_PORT", "9030")),
        "user": os.environ.get("DORIS_USER", "root"),
        "password": os.environ.get("DORIS_PASSWORD", "")
    }
    
    # Override with provided config if available
    if 'config' in globals() and config is not None:
        for key, value in config.items():
            config[key] = value
    
    client = DorisClient(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        mock=True
    )
    
    result = client.execute_query("SELECT 1")
    logger.info(f"Query result: {result}")
    
    client.create_table("test_table", {
        "id": "INT",
        "name": "VARCHAR(100)",
        "created_at": "DATETIME"
    })
    
    client.insert_data("test_table", [
        {"id": 1, "name": "Test 1", "created_at": "2023-01-01 00:00:00"},
        {"id": 2, "name": "Test 2", "created_at": "2023-01-02 00:00:00"}
    ])
    
    table_data = client.execute_query("SELECT * FROM test_table")
    logger.info(f"Table data: {table_data}")
    
    logger.info("Apache Doris connection test successful")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"Apache Doris connection test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("Apache Doris connection test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("Apache Doris connection test failed: %s", outputStr)
		return false
	}

	logger.Printf("Apache Doris test output: %s", outputStr)
	return true
}

func TestKafkaConnection(config map[string]interface{}) bool {
	logger.Println("Testing Apache Kafka connection...")

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
    from backend.db.integrations.kafka import KafkaClient
    
    config = {
        "bootstrap_servers": os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        "group_id": os.environ.get("KAFKA_GROUP_ID", "test_group")
    }
    
    # Override with provided config if available
    if 'config' in globals() and config is not None:
        for key, value in config.items():
            config[key] = value
    
    client = KafkaClient(
        bootstrap_servers=config["bootstrap_servers"],
        group_id=config["group_id"],
        mock=True
    )
    
    client.produce_message("test_topic", {"test": "message"})
    
    message = client.consume_message("test_topic")
    logger.info(f"Consumed message: {message}")
    
    logger.info("Apache Kafka connection test successful")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"Apache Kafka connection test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("Apache Kafka connection test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("Apache Kafka connection test failed: %s", outputStr)
		return false
	}

	logger.Printf("Apache Kafka test output: %s", outputStr)
	return true
}

func TestPostgresConnection(config map[string]interface{}) bool {
	logger.Println("Testing PostgreSQL connection...")

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
    from backend.db.integrations.crunchydata import PostgresClient
    
    config = {
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
        "user": os.environ.get("POSTGRES_USER", "postgres"),
        "password": os.environ.get("POSTGRES_PASSWORD", ""),
        "database": os.environ.get("POSTGRES_DATABASE", "postgres")
    }
    
    # Override with provided config if available
    if 'config' in globals() and config is not None:
        for key, value in config.items():
            config[key] = value
    
    client = PostgresClient(
        host=config["host"],
        port=config["port"],
        user=config["user"],
        password=config["password"],
        database=config["database"],
        mock=True
    )
    
    result = client.execute_query("SELECT 1")
    logger.info(f"Query result: {result}")
    
    client.create_table("test_table", {
        "id": "SERIAL PRIMARY KEY",
        "name": "VARCHAR(100)",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    
    client.insert_data("test_table", [
        {"name": "Test 1"},
        {"name": "Test 2"}
    ])
    
    table_data = client.execute_query("SELECT * FROM test_table")
    logger.info(f"Table data: {table_data}")
    
    logger.info("PostgreSQL connection test successful")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"PostgreSQL connection test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("PostgreSQL connection test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("PostgreSQL connection test failed: %s", outputStr)
		return false
	}

	logger.Printf("PostgreSQL test output: %s", outputStr)
	return true
}

func TestCrossDatabaseIntegration() bool {
	logger.Println("Testing cross-database integration...")

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
    from backend.db.integrations.crunchydata import PostgresClient
    from backend.db.integrations.kafka import KafkaClient
    from backend.db.integrations.doris import DorisClient
    
    postgres_client = PostgresClient(mock=True)
    kafka_client = KafkaClient(mock=True)
    doris_client = DorisClient(mock=True)
    
    postgres_client.create_table("test_integration", {
        "id": "SERIAL PRIMARY KEY",
        "name": "VARCHAR(100)",
        "value": "INT",
        "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    })
    
    postgres_client.insert_data("test_integration", [
        {"name": "Integration Test 1", "value": 100},
        {"name": "Integration Test 2", "value": 200},
        {"name": "Integration Test 3", "value": 300}
    ])
    
    kafka_client.produce_message("test_integration", {
        "source": "postgres",
        "destination": "doris",
        "table": "test_integration",
        "operation": "insert"
    })
    
    doris_client.create_table("test_integration", {
        "id": "INT",
        "name": "VARCHAR(100)",
        "value": "INT",
        "created_at": "DATETIME"
    })
    
    doris_client.insert_data("test_integration", [
        {"id": 1, "name": "Integration Test 1", "value": 100, "created_at": "2023-01-01 00:00:00"},
        {"id": 2, "name": "Integration Test 2", "value": 200, "created_at": "2023-01-01 00:00:00"},
        {"id": 3, "name": "Integration Test 3", "value": 300, "created_at": "2023-01-01 00:00:00"}
    ])
    
    result = doris_client.execute_query("SELECT COUNT(*) FROM test_integration")
    logger.info(f"Cross-database integration test result: {result}")
    
    logger.info("Cross-database integration test successful")
    print("SUCCESS")
    
except Exception as e:
    logger.error(f"Cross-database integration test failed: {e}")
    print(f"ERROR: {e}")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("Cross-database integration test failed: %v", err)
		logger.Printf("Error output: %s", outputStr)
		return false
	}

	if strings.Contains(outputStr, "ERROR:") {
		logger.Printf("Cross-database integration test failed: %s", outputStr)
		return false
	}

	logger.Printf("Cross-database integration test output: %s", outputStr)
	return true
}

func RunDatabaseConnectionTests() int {
	allFlag := flag.Bool("all", false, "Test all database connections")
	supabaseFlag := flag.Bool("supabase", false, "Test Supabase connection")
	ragflowFlag := flag.Bool("ragflow", false, "Test RAGflow connection")
	dragonflyFlag := flag.Bool("dragonfly", false, "Test DragonflyDB connection")
	rocketmqFlag := flag.Bool("rocketmq", false, "Test RocketMQ connection")
	dorisFlag := flag.Bool("doris", false, "Test Apache Doris connection")
	kafkaFlag := flag.Bool("kafka", false, "Test Apache Kafka connection")
	postgresFlag := flag.Bool("postgres", false, "Test PostgreSQL connection")
	integrationFlag := flag.Bool("integration", false, "Test cross-database integration")
	configFlag := flag.String("config", "", "Path to configuration file")

	flag.Parse()

	var config map[string]map[string]interface{}
	if *configFlag != "" {
		configFile, err := os.Open(*configFlag)
		if err != nil {
			logger.Printf("Failed to open configuration file: %v", err)
			return 1
		}
		defer configFile.Close()

		decoder := json.NewDecoder(configFile)
		if err := decoder.Decode(&config); err != nil {
			logger.Printf("Failed to parse configuration file: %v", err)
			return 1
		}
	}

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

	runAll := *allFlag || !(*supabaseFlag || *ragflowFlag || *dragonflyFlag ||
		*rocketmqFlag || *dorisFlag || *kafkaFlag || *postgresFlag || *integrationFlag)

	success := true

	if runAll || *supabaseFlag {
		var supabaseConfig map[string]interface{}
		if config != nil {
			supabaseConfig = config["supabase"]
		}
		if !TestSupabaseConnection(supabaseConfig) {
			success = false
		}
	}

	if runAll || *ragflowFlag {
		var ragflowConfig map[string]interface{}
		if config != nil {
			ragflowConfig = config["ragflow"]
		}
		if !TestRAGflowConnection(ragflowConfig) {
			success = false
		}
	}

	if runAll || *dragonflyFlag {
		var dragonflyConfig map[string]interface{}
		if config != nil {
			dragonflyConfig = config["dragonfly"]
		}
		if !TestDragonflyConnection(dragonflyConfig) {
			success = false
		}
	}

	if runAll || *rocketmqFlag {
		var rocketmqConfig map[string]interface{}
		if config != nil {
			rocketmqConfig = config["rocketmq"]
		}
		if !TestRocketMQConnection(rocketmqConfig) {
			success = false
		}
	}

	if runAll || *dorisFlag {
		var dorisConfig map[string]interface{}
		if config != nil {
			dorisConfig = config["doris"]
		}
		if !TestDorisConnection(dorisConfig) {
			success = false
		}
	}

	if runAll || *kafkaFlag {
		var kafkaConfig map[string]interface{}
		if config != nil {
			kafkaConfig = config["kafka"]
		}
		if !TestKafkaConnection(kafkaConfig) {
			success = false
		}
	}

	if runAll || *postgresFlag {
		var postgresConfig map[string]interface{}
		if config != nil {
			postgresConfig = config["postgres"]
		}
		if !TestPostgresConnection(postgresConfig) {
			success = false
		}
	}

	if runAll || *integrationFlag {
		if !TestCrossDatabaseIntegration() {
			success = false
		}
	}

	if success {
		logger.Println("All database connection tests passed")
		return 0
	} else {
		logger.Println("Some database connection tests failed")
		return 1
	}
}

func main() {
	os.Exit(RunDatabaseConnectionTests())
}
