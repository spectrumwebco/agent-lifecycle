package scripts

import (
	"flag"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var verificationLogger *log.Logger

func init() {
	logFile, err := os.OpenFile("database_verification.log", os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}

	verificationLogger = log.New(os.Stdout, "", log.LstdFlags)
	fileLogger := log.New(logFile, "", log.LstdFlags)

	defaultLogFunc := verificationLogger.Println
	verificationLogger.Println = func(v ...interface{}) {
		defaultLogFunc(v...)
		fileLogger.Println(v...)
	}
}

func RunCommand(command, description string) (bool, string) {
	verificationLogger.Printf("Running %s...", description)

	cmd := exec.Command("bash", "-c", command)
	cmd.Env = os.Environ()

	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		verificationLogger.Printf("%s failed with error: %v", description, err)
		verificationLogger.Printf("Error output: %s", outputStr)
		return false, outputStr
	}

	verificationLogger.Printf("%s completed successfully", description)
	verificationLogger.Printf("Output: %s", outputStr)
	return true, outputStr
}

func VerifyDatabaseConnections() bool {
	verificationLogger.Println("Verifying database connections...")

	success, output := RunCommand(
		"python manage.py check --database=default",
		"Django database configuration check for Apache Doris",
	)
	if !success {
		verificationLogger.Println("Database configuration check failed for Apache Doris")
		return false
	}

	success, output = RunCommand(
		"python manage.py check --database=agent_db",
		"Django database configuration check for PostgreSQL",
	)
	if !success {
		verificationLogger.Println("Database configuration check failed for PostgreSQL")
		return false
	}

	success, output = RunCommand(
		"python manage.py verify_database_integration --all",
		"Database integration verification",
	)
	if !success {
		verificationLogger.Println("Database integration verification failed")
		return false
	}

	verificationLogger.Println("All database connections verified successfully")
	return true
}

func RunDatabaseTests() bool {
	verificationLogger.Println("Running database integration tests...")

	success, output := RunCommand(
		"python manage.py test apps.python_agent.tests.test_database_models",
		"Database model tests",
	)
	if !success {
		verificationLogger.Println("Database model tests failed")
		return false
	}

	success, output = RunCommand(
		"python manage.py test apps.python_agent.tests.test_database_integration",
		"Database integration tests",
	)
	if !success {
		verificationLogger.Println("Database integration tests failed")
		return false
	}

	verificationLogger.Println("All database tests passed successfully")
	return true
}

func VerifyKafkaIntegration() bool {
	verificationLogger.Println("Verifying Kafka integration...")

	success, output := RunCommand(
		"python manage.py verify_database_integration --kafka",
		"Kafka integration verification",
	)
	if !success {
		verificationLogger.Println("Kafka integration verification failed")
		return false
	}

	kafkaScript := `
from backend.integrations.kafka import KafkaClient
client = KafkaClient()
client.produce_message('test-topic', {'message': 'test'})
print('Message produced successfully')
message = client.consume_message('test-topic', timeout=10)
print(f'Message consumed: {message}')
`

	cmd := db.ExecutePythonScript(kafkaScript)
	output, err := cmd.CombinedOutput()
	if err != nil {
		verificationLogger.Printf("Kafka message production and consumption test failed: %v", err)
		verificationLogger.Printf("Output: %s", string(output))
		return false
	}

	verificationLogger.Printf("Kafka message production and consumption test output: %s", string(output))
	verificationLogger.Println("Kafka integration verified successfully")
	return true
}

func VerifyPostgresIntegration() bool {
	verificationLogger.Println("Verifying PostgreSQL integration...")

	success, output := RunCommand(
		"python manage.py verify_database_integration --postgres",
		"PostgreSQL integration verification",
	)
	if !success {
		verificationLogger.Println("PostgreSQL integration verification failed")
		return false
	}

	success, output = RunCommand(
		"python manage.py setup_postgres --check",
		"PostgreSQL cluster management test",
	)
	if !success {
		verificationLogger.Println("PostgreSQL cluster management test failed")
		return false
	}

	verificationLogger.Println("PostgreSQL integration verified successfully")
	return true
}

func VerifyDorisIntegration() bool {
	verificationLogger.Println("Verifying Apache Doris integration...")

	success, output := RunCommand(
		"python manage.py verify_database_integration --doris",
		"Apache Doris integration verification",
	)
	if !success {
		verificationLogger.Println("Apache Doris integration verification failed")
		return false
	}

	dorisScript := `
from django.db import connections
cursor = connections['default'].cursor()
cursor.execute('SELECT VERSION()')
version = cursor.fetchone()[0]
print(f'Apache Doris version: {version}')
cursor.execute('SHOW DATABASES')
databases = cursor.fetchall()
print(f'Databases: {databases}')
`

	cmd := db.ExecutePythonScript(dorisScript)
	output, err := cmd.CombinedOutput()
	if err != nil {
		verificationLogger.Printf("Apache Doris query capabilities test failed: %v", err)
		verificationLogger.Printf("Output: %s", string(output))
		return false
	}

	verificationLogger.Printf("Apache Doris query capabilities test output: %s", string(output))
	verificationLogger.Println("Apache Doris integration verified successfully")
	return true
}

func VerifyCrossDatabaseIntegration() bool {
	verificationLogger.Println("Verifying cross-database integration...")

	success, output := RunCommand(
		"python manage.py verify_database_integration --integration",
		"Cross-database integration verification",
	)
	if !success {
		verificationLogger.Println("Cross-database integration verification failed")
		return false
	}

	verificationLogger.Println("Cross-database integration verified successfully")
	return true
}

func RunDatabaseVerification() int {
	allFlag := flag.Bool("all", false, "Run all verification tests")
	connectionsFlag := flag.Bool("connections", false, "Verify database connections")
	testsFlag := flag.Bool("tests", false, "Run database tests")
	kafkaFlag := flag.Bool("kafka", false, "Verify Kafka integration")
	postgresFlag := flag.Bool("postgres", false, "Verify PostgreSQL integration")
	dorisFlag := flag.Bool("doris", false, "Verify Apache Doris integration")
	crossFlag := flag.Bool("cross", false, "Verify cross-database integration")

	flag.Parse()

	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		verificationLogger.Printf("Error getting current directory: %v", err)
		return 1
	}
	err = os.Chdir(dir)
	if err != nil {
		verificationLogger.Printf("Error changing directory: %v", err)
		return 1
	}

	runAll := *allFlag || !(*connectionsFlag || *testsFlag || *kafkaFlag ||
		*postgresFlag || *dorisFlag || *crossFlag)

	success := true

	if runAll || *connectionsFlag {
		if !VerifyDatabaseConnections() {
			success = false
		}
	}

	if runAll || *testsFlag {
		if !RunDatabaseTests() {
			success = false
		}
	}

	if runAll || *kafkaFlag {
		if !VerifyKafkaIntegration() {
			success = false
		}
	}

	if runAll || *postgresFlag {
		if !VerifyPostgresIntegration() {
			success = false
		}
	}

	if runAll || *dorisFlag {
		if !VerifyDorisIntegration() {
			success = false
		}
	}

	if runAll || *crossFlag {
		if !VerifyCrossDatabaseIntegration() {
			success = false
		}
	}

	if success {
		verificationLogger.Println("All database verification tests passed successfully")
		return 0
	} else {
		verificationLogger.Println("Some database verification tests failed")
		return 1
	}
}

func main() {
	os.Exit(RunDatabaseVerification())
}
