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
)

var logger *log.Logger

func init() {
	timestamp := time.Now().Format("20060102_150405")
	logFile, err := os.Create(fmt.Sprintf("database_tests_%s.log", timestamp))
	if err != nil {
		log.Fatalf("Failed to create log file: %v", err)
	}

	logger = log.New(os.Stdout, "", log.LstdFlags)
	fileLogger := log.New(logFile, "", log.LstdFlags)

	log.SetOutput(os.Stdout)
	log.SetFlags(log.LstdFlags)

	defaultLogFunc := logger.Println
	logger.Println = func(v ...interface{}) {
		defaultLogFunc(v...)
		fileLogger.Println(v...)
	}
}

func RunCommand(command, description string) (bool, string) {
	logger.Printf("Running %s...", description)

	cmd := exec.Command("bash", "-c", command)
	cmd.Env = os.Environ()

	output, err := cmd.CombinedOutput()
	outputStr := string(output)

	if err != nil {
		logger.Printf("%s failed with error: %v", description, err)
		logger.Printf("Error output: %s", outputStr)
		return false, outputStr
	}

	logger.Printf("%s completed successfully", description)
	logger.Printf("Output: %s", outputStr)
	return true, outputStr
}

func TestAllDatabases() bool {
	logger.Println("Testing all database systems...")

	success, _ := RunCommand(
		"python manage.py test_all_databases --all",
		"All database systems test",
	)

	if !success {
		logger.Println("All database systems test failed")
		return false
	}

	logger.Println("All database systems test completed successfully")
	return true
}

func TestSupabase() bool {
	logger.Println("Testing Supabase integration...")

	success, _ := RunCommand(
		"python manage.py test_all_databases --supabase",
		"Supabase integration test",
	)

	if !success {
		logger.Println("Supabase integration test failed")
		return false
	}

	logger.Println("Supabase integration test completed successfully")
	return true
}

func TestRAGflow() bool {
	logger.Println("Testing RAGflow integration...")

	success, _ := RunCommand(
		"python manage.py test_all_databases --ragflow",
		"RAGflow integration test",
	)

	if !success {
		logger.Println("RAGflow integration test failed")
		return false
	}

	logger.Println("RAGflow integration test completed successfully")
	return true
}

func TestDragonfly() bool {
	logger.Println("Testing DragonflyDB integration...")

	success, _ := RunCommand(
		"python manage.py test_all_databases --dragonfly",
		"DragonflyDB integration test",
	)

	if !success {
		logger.Println("DragonflyDB integration test failed")
		return false
	}

	logger.Println("DragonflyDB integration test completed successfully")
	return true
}

func TestRocketMQ() bool {
	logger.Println("Testing RocketMQ integration...")

	success, _ := RunCommand(
		"python manage.py test_all_databases --rocketmq",
		"RocketMQ integration test",
	)

	if !success {
		logger.Println("RocketMQ integration test failed")
		return false
	}

	logger.Println("RocketMQ integration test completed successfully")
	return true
}

func TestDoris() bool {
	logger.Println("Testing Apache Doris integration...")

	success, _ := RunCommand(
		"python manage.py test_all_databases --doris",
		"Apache Doris integration test",
	)

	if !success {
		logger.Println("Apache Doris integration test failed")
		return false
	}

	logger.Println("Apache Doris integration test completed successfully")
	return true
}

func TestPostgres() bool {
	logger.Println("Testing PostgreSQL integration...")

	success, _ := RunCommand(
		"python manage.py test_all_databases --postgres",
		"PostgreSQL integration test",
	)

	if !success {
		logger.Println("PostgreSQL integration test failed")
		return false
	}

	logger.Println("PostgreSQL integration test completed successfully")
	return true
}

func TestKafka() bool {
	logger.Println("Testing Kafka integration...")

	success, _ := RunCommand(
		"python manage.py test_all_databases --kafka",
		"Kafka integration test",
	)

	if !success {
		logger.Println("Kafka integration test failed")
		return false
	}

	logger.Println("Kafka integration test completed successfully")
	return true
}

func RunDjangoTests() bool {
	logger.Println("Running Django test suite for database integration...")

	success, _ := RunCommand(
		"python manage.py test apps.python_agent.tests.test_database_integration",
		"Django database integration tests",
	)

	if !success {
		logger.Println("Django database integration tests failed")
		return false
	}

	success, _ = RunCommand(
		"python manage.py test apps.python_agent.tests.test_database_models",
		"Django database models tests",
	)

	if !success {
		logger.Println("Django database models tests failed")
		return false
	}

	logger.Println("Django test suite for database integration completed successfully")
	return true
}

func VerifyDatabaseIntegration() bool {
	logger.Println("Verifying database integration...")

	success, _ := RunCommand(
		"python manage.py verify_database_integration --all",
		"Database integration verification",
	)

	if !success {
		logger.Println("Database integration verification failed")
		return false
	}

	logger.Println("Database integration verification completed successfully")
	return true
}

func Main() int {
	allFlag := flag.Bool("all", false, "Run all tests")
	supabaseFlag := flag.Bool("supabase", false, "Test Supabase integration")
	ragflowFlag := flag.Bool("ragflow", false, "Test RAGflow integration")
	dragonflyFlag := flag.Bool("dragonfly", false, "Test DragonflyDB integration")
	rocketmqFlag := flag.Bool("rocketmq", false, "Test RocketMQ integration")
	dorisFlag := flag.Bool("doris", false, "Test Apache Doris integration")
	postgresFlag := flag.Bool("postgres", false, "Test PostgreSQL integration")
	kafkaFlag := flag.Bool("kafka", false, "Test Kafka integration")
	djangoFlag := flag.Bool("django", false, "Run Django test suite")
	verifyFlag := flag.Bool("verify", false, "Verify database integration")

	flag.Parse()

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

	os.Setenv("DJANGO_SETTINGS_MODULE", "agent_api.settings")

	runAll := *allFlag || !(*supabaseFlag || *ragflowFlag || *dragonflyFlag || *rocketmqFlag ||
		*dorisFlag || *postgresFlag || *kafkaFlag || *djangoFlag || *verifyFlag)

	success := true

	if runAll || *supabaseFlag {
		if !TestSupabase() {
			success = false
		}
	}

	if runAll || *ragflowFlag {
		if !TestRAGflow() {
			success = false
		}
	}

	if runAll || *dragonflyFlag {
		if !TestDragonfly() {
			success = false
		}
	}

	if runAll || *rocketmqFlag {
		if !TestRocketMQ() {
			success = false
		}
	}

	if runAll || *dorisFlag {
		if !TestDoris() {
			success = false
		}
	}

	if runAll || *postgresFlag {
		if !TestPostgres() {
			success = false
		}
	}

	if runAll || *kafkaFlag {
		if !TestKafka() {
			success = false
		}
	}

	if runAll || *djangoFlag {
		if !RunDjangoTests() {
			success = false
		}
	}

	if runAll || *verifyFlag {
		if !VerifyDatabaseIntegration() {
			success = false
		}
	}

	if success {
		logger.Println("All tests completed successfully")
		return 0
	} else {
		logger.Println("Some tests failed")
		return 1
	}
}

func main() {
	os.Exit(Main())
}
