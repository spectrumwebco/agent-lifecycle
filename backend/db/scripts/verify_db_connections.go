package scripts

import (
	"fmt"
	"log"
	"net"
	"os"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var verifyLogger = log.New(os.Stdout, "", log.LstdFlags)

func IsRunningInKubernetes() bool {
	_, err := os.Stat("/var/run/secrets/kubernetes.io/serviceaccount/token")
	return err == nil
}

var (
	InKubernetes = IsRunningInKubernetes()
	Env          = "kubernetes"
)

func init() {
	if !InKubernetes {
		Env = "local"
	}
}

type DatabaseConfig struct {
	Environment    string
	DBHost         string
	DBPort         int
	DBUser         string
	DBPassword     string
	DBName         string
	MariaDBHost    string
	MariaDBPort    int
	MariaDBUser    string
	MariaDBPassword string
	MariaDBName    string
	RedisHost      string
	RedisPort      int
	RAGflowHost    string
	RAGflowPort    int
	RocketMQHost   string
	RocketMQPort   int
}

func NewDatabaseConfig() *DatabaseConfig {
	config := &DatabaseConfig{
		Environment: Env,
		DBUser:      "postgres",
		DBPassword:  "postgres",
		DBName:      "postgres",
		DBPort:      5432,
		MariaDBHost: "localhost",
		MariaDBPort: 3306,
		MariaDBUser: "agent_user",
		MariaDBPassword: "agent_password",
		MariaDBName: "agent_runtime",
		RedisPort:   6379,
		RAGflowPort: 8000,
		RocketMQPort: 9876,
	}

	if InKubernetes {
		config.DBHost = "supabase-db.default.svc.cluster.local"
		config.RedisHost = "dragonfly-db.default.svc.cluster.local"
		config.RAGflowHost = "ragflow.default.svc.cluster.local"
		config.RocketMQHost = "rocketmq.default.svc.cluster.local"
	} else {
		config.DBHost = "localhost"
		config.RedisHost = "localhost"
		config.RAGflowHost = "localhost"
		config.RocketMQHost = "localhost"
	}

	return config
}

var dbConfig = NewDatabaseConfig()

func CheckPortOpen(host string, port int, timeout time.Duration) bool {
	address := fmt.Sprintf("%s:%d", host, port)
	conn, err := net.DialTimeout("tcp", address, timeout)
	if err != nil {
		verifyLogger.Printf("Error checking port %d on %s: %v", port, host, err)
		return false
	}
	defer conn.Close()
	return true
}

func CheckPostgresConnection() bool {
	verifyLogger.Println("Checking PostgreSQL connection...")

	pgScript := `
import os
import sys
import psycopg2

try:
    conn = psycopg2.connect(
        host="%s",
        port=%d,
        user="%s",
        password="%s",
        dbname="%s",
        connect_timeout=3
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"Connected to PostgreSQL: {version[0]}")
    
    cursor.close()
    conn.close()
    sys.exit(0)
except ImportError:
    print("psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"PostgreSQL connection failed: {e}")
    sys.exit(1)
`
	pgScript = fmt.Sprintf(pgScript, dbConfig.DBHost, dbConfig.DBPort, dbConfig.DBUser, dbConfig.DBPassword, dbConfig.DBName)

	cmd := db.ExecutePythonScript(pgScript)
	output, err := cmd.CombinedOutput()
	if err != nil {
		verifyLogger.Printf("PostgreSQL connection failed: %v", err)
		verifyLogger.Printf("Output: %s", string(output))
		return false
	}

	verifyLogger.Printf("PostgreSQL connection output: %s", string(output))
	return true
}

func CheckMariaDBConnection() bool {
	verifyLogger.Println("Checking MariaDB connection...")

	mariaScript := `
import os
import sys
import MySQLdb

try:
    conn = MySQLdb.connect(
        host="%s",
        port=%d,
        user="%s",
        passwd="%s",
        db="%s",
        connect_timeout=3
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION();")
    version = cursor.fetchone()
    print(f"Connected to MariaDB: {version[0]}")
    
    cursor.close()
    conn.close()
    sys.exit(0)
except ImportError:
    print("MySQLdb not installed. Install with: pip install mysqlclient")
    sys.exit(1)
except Exception as e:
    print(f"MariaDB connection failed: {e}")
    
    if "Unknown database" in str(e):
        try:
            print("Attempting to create database and user...")
            
            conn = MySQLdb.connect(
                host="%s",
                port=%d,
                user="root",
                passwd="",
                connect_timeout=3
            )
            
            cursor = conn.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS %s;")
            
            cursor.execute("CREATE USER IF NOT EXISTS '%s'@'localhost' IDENTIFIED BY '%s';")
            
            cursor.execute("GRANT ALL PRIVILEGES ON %s.* TO '%s'@'localhost';")
            cursor.execute("FLUSH PRIVILEGES;")
            
            cursor.close()
            conn.close()
            
            print("Database and user created successfully. Retrying connection...")
            
            conn = MySQLdb.connect(
                host="%s",
                port=%d,
                user="%s",
                passwd="%s",
                db="%s",
                connect_timeout=3
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION();")
            version = cursor.fetchone()
            print(f"Connected to MariaDB: {version[0]}")
            
            cursor.close()
            conn.close()
            sys.exit(0)
        except Exception as setup_error:
            print(f"Failed to set up MariaDB: {setup_error}")
            sys.exit(1)
    
    sys.exit(1)
`
	mariaScript = fmt.Sprintf(mariaScript, 
		dbConfig.MariaDBHost, dbConfig.MariaDBPort, dbConfig.MariaDBUser, dbConfig.MariaDBPassword, dbConfig.MariaDBName,
		dbConfig.MariaDBHost, dbConfig.MariaDBPort, dbConfig.MariaDBName,
		dbConfig.MariaDBUser, dbConfig.MariaDBPassword, dbConfig.MariaDBName, dbConfig.MariaDBUser,
		dbConfig.MariaDBHost, dbConfig.MariaDBPort, dbConfig.MariaDBUser, dbConfig.MariaDBPassword, dbConfig.MariaDBName)

	cmd := db.ExecutePythonScript(mariaScript)
	output, err := cmd.CombinedOutput()
	if err != nil {
		verifyLogger.Printf("MariaDB connection failed: %v", err)
		verifyLogger.Printf("Output: %s", string(output))
		return false
	}

	verifyLogger.Printf("MariaDB connection output: %s", string(output))
	return true
}

func CheckRedisConnection() bool {
	verifyLogger.Println("Checking Redis (DragonflyDB) connection...")

	redisScript := `
import os
import sys
import redis

try:
    r = redis.Redis(
        host="%s",
        port=%d,
        socket_timeout=3
    )
    
    pong = r.ping()
    print(f"Connected to Redis: {pong}")
    sys.exit(0)
except ImportError:
    print("redis not installed. Install with: pip install redis")
    sys.exit(1)
except Exception as e:
    print(f"Redis connection failed: {e}")
    sys.exit(1)
`
	redisScript = fmt.Sprintf(redisScript, dbConfig.RedisHost, dbConfig.RedisPort)

	cmd := db.ExecutePythonScript(redisScript)
	output, err := cmd.CombinedOutput()
	if err != nil {
		verifyLogger.Printf("Redis connection failed: %v", err)
		verifyLogger.Printf("Output: %s", string(output))
		return false
	}

	verifyLogger.Printf("Redis connection output: %s", string(output))
	return true
}

func CheckRAGflowConnection() bool {
	verifyLogger.Println("Checking RAGflow connection...")

	ragflowScript := `
import os
import sys
import requests

try:
    response = requests.get(
        f"http://%s:%d/health",
        timeout=3
    )
    
    if response.status_code == 200:
        print(f"Connected to RAGflow: {response.json()}")
        sys.exit(0)
    else:
        print(f"RAGflow returned status code: {response.status_code}")
        sys.exit(1)
except ImportError:
    print("requests not installed. Install with: pip install requests")
    sys.exit(1)
except Exception as e:
    print(f"RAGflow connection failed: {e}")
    sys.exit(1)
`
	ragflowScript = fmt.Sprintf(ragflowScript, dbConfig.RAGflowHost, dbConfig.RAGflowPort)

	cmd := db.ExecutePythonScript(ragflowScript)
	output, err := cmd.CombinedOutput()
	if err != nil {
		verifyLogger.Printf("RAGflow connection failed: %v", err)
		verifyLogger.Printf("Output: %s", string(output))
		return false
	}

	verifyLogger.Printf("RAGflow connection output: %s", string(output))
	return true
}

func CheckRocketMQConnection() bool {
	verifyLogger.Println("Checking RocketMQ connection...")

	if CheckPortOpen(dbConfig.RocketMQHost, dbConfig.RocketMQPort, 3*time.Second) {
		verifyLogger.Println("RocketMQ port is open")
		return true
	} else {
		verifyLogger.Println("RocketMQ port is closed")
		return false
	}
}

func VerifyDatabaseConnections() int {
	fmt.Println("\n=== Database Connection Verification ===\n")
	
	fmt.Printf("Environment: %s\n", Env)
	fmt.Printf("Running in Kubernetes: %t\n\n", InKubernetes)
	
	fmt.Println("\n=== PostgreSQL (Supabase) Connection ===")
	postgresOK := CheckPostgresConnection()
	fmt.Printf("PostgreSQL connection: %s\n", formatStatus(postgresOK))
	
	var mariadbOK bool
	if Env == "local" {
		fmt.Println("\n=== MariaDB Connection (Local Development) ===")
		mariadbOK = CheckMariaDBConnection()
		fmt.Printf("MariaDB connection: %s\n", formatStatus(mariadbOK))
	}
	
	fmt.Println("\n=== Redis (DragonflyDB) Connection ===")
	redisOK := CheckRedisConnection()
	fmt.Printf("Redis connection: %s\n", formatStatus(redisOK))
	
	fmt.Println("\n=== RAGflow Connection ===")
	ragflowOK := CheckRAGflowConnection()
	fmt.Printf("RAGflow connection: %s\n", formatStatus(ragflowOK))
	
	fmt.Println("\n=== RocketMQ Connection ===")
	rocketmqOK := CheckRocketMQConnection()
	fmt.Printf("RocketMQ connection: %s\n", formatStatus(rocketmqOK))
	
	fmt.Println("\n=== Connection Summary ===")
	if Env == "local" {
		fmt.Printf("PostgreSQL: %s\n", formatStatusEmoji(postgresOK))
		fmt.Printf("MariaDB: %s\n", formatStatusEmoji(mariadbOK))
		fmt.Printf("Redis: %s\n", formatStatusEmoji(redisOK))
		fmt.Printf("RAGflow: %s\n", formatStatusEmoji(ragflowOK))
		fmt.Printf("RocketMQ: %s\n", formatStatusEmoji(rocketmqOK))
		
		if !postgresOK && !mariadbOK {
			fmt.Println("\n⚠️ No database connections available. Please set up at least one database.")
		} else if !postgresOK && mariadbOK {
			fmt.Println("\n✅ MariaDB is available for local development.")
		} else if postgresOK && !mariadbOK {
			fmt.Println("\n✅ PostgreSQL is available for local development.")
		} else {
			fmt.Println("\n✅ Both PostgreSQL and MariaDB are available.")
		}
	} else {
		fmt.Printf("PostgreSQL: %s\n", formatStatusEmoji(postgresOK))
		fmt.Printf("Redis: %s\n", formatStatusEmoji(redisOK))
		fmt.Printf("RAGflow: %s\n", formatStatusEmoji(ragflowOK))
		fmt.Printf("RocketMQ: %s\n", formatStatusEmoji(rocketmqOK))
		
		if !postgresOK {
			fmt.Println("\n⚠️ PostgreSQL connection failed. Please check your Kubernetes configuration.")
		}
	}

	if (Env == "local" && (postgresOK || mariadbOK)) || (Env == "kubernetes" && postgresOK) {
		return 0
	}
	return 1
}

func formatStatus(ok bool) string {
	if ok {
		return "✅ OK"
	}
	return "❌ Failed"
}

func formatStatusEmoji(ok bool) string {
	if ok {
		return "✅"
	}
	return "❌"
}

func main() {
	os.Exit(VerifyDatabaseConnections())
}
