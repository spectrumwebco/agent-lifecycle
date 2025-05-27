

cd "$(dirname "$0")"
export DJANGO_SETTINGS_MODULE=agent_api.settings

ALL=false
SUPABASE=false
RAGFLOW=false
DRAGONFLY=false
ROCKETMQ=false
DORIS=false
POSTGRES=false
KAFKA=false
DJANGO=false
VERIFY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --all)
      ALL=true
      shift
      ;;
    --supabase)
      SUPABASE=true
      shift
      ;;
    --ragflow)
      RAGFLOW=true
      shift
      ;;
    --dragonfly)
      DRAGONFLY=true
      shift
      ;;
    --rocketmq)
      ROCKETMQ=true
      shift
      ;;
    --doris)
      DORIS=true
      shift
      ;;
    --postgres)
      POSTGRES=true
      shift
      ;;
    --kafka)
      KAFKA=true
      shift
      ;;
    --django)
      DJANGO=true
      shift
      ;;
    --verify)
      VERIFY=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--all] [--supabase] [--ragflow] [--dragonfly] [--rocketmq] [--doris] [--postgres] [--kafka] [--django] [--verify]"
      exit 1
      ;;
  esac
done

if [ "$ALL" = false ] && [ "$SUPABASE" = false ] && [ "$RAGFLOW" = false ] && [ "$DRAGONFLY" = false ] && [ "$ROCKETMQ" = false ] && [ "$DORIS" = false ] && [ "$POSTGRES" = false ] && [ "$KAFKA" = false ] && [ "$DJANGO" = false ] && [ "$VERIFY" = false ]; then
  ALL=true
fi

LOG_FILE="database_tests_$(date +%Y%m%d_%H%M%S).log"
echo "Starting database integration tests at $(date)" | tee -a "$LOG_FILE"

run_command() {
  local description="$1"
  local command="$2"
  
  echo "Running $description..." | tee -a "$LOG_FILE"
  if eval "$command" >> "$LOG_FILE" 2>&1; then
    echo "$description completed successfully" | tee -a "$LOG_FILE"
    return 0
  else
    echo "$description failed" | tee -a "$LOG_FILE"
    return 1
  fi
}

test_supabase() {
  echo "Testing Supabase integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "Supabase integration test" "python manage.py test_all_databases --supabase"; then
    echo "Supabase integration test failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "Supabase integration test completed successfully" | tee -a "$LOG_FILE"
  return 0
}

test_ragflow() {
  echo "Testing RAGflow integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "RAGflow integration test" "python manage.py test_all_databases --ragflow"; then
    echo "RAGflow integration test failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "RAGflow integration test completed successfully" | tee -a "$LOG_FILE"
  return 0
}

test_dragonfly() {
  echo "Testing DragonflyDB integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "DragonflyDB integration test" "python manage.py test_all_databases --dragonfly"; then
    echo "DragonflyDB integration test failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "DragonflyDB integration test completed successfully" | tee -a "$LOG_FILE"
  return 0
}

test_rocketmq() {
  echo "Testing RocketMQ integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "RocketMQ integration test" "python manage.py test_all_databases --rocketmq"; then
    echo "RocketMQ integration test failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "RocketMQ integration test completed successfully" | tee -a "$LOG_FILE"
  return 0
}

test_doris() {
  echo "Testing Apache Doris integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "Apache Doris integration test" "python manage.py test_all_databases --doris"; then
    echo "Apache Doris integration test failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "Apache Doris integration test completed successfully" | tee -a "$LOG_FILE"
  return 0
}

test_postgres() {
  echo "Testing PostgreSQL integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "PostgreSQL integration test" "python manage.py test_all_databases --postgres"; then
    echo "PostgreSQL integration test failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "PostgreSQL integration test completed successfully" | tee -a "$LOG_FILE"
  return 0
}

test_kafka() {
  echo "Testing Kafka integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "Kafka integration test" "python manage.py test_all_databases --kafka"; then
    echo "Kafka integration test failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "Kafka integration test completed successfully" | tee -a "$LOG_FILE"
  return 0
}

run_django_tests() {
  echo "Running Django test suite for database integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "Django database integration tests" "python manage.py test apps.python_agent.tests.test_database_integration"; then
    echo "Django database integration tests failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  if ! run_command "Django database models tests" "python manage.py test apps.python_agent.tests.test_database_models"; then
    echo "Django database models tests failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "Django test suite for database integration completed successfully" | tee -a "$LOG_FILE"
  return 0
}

verify_database_integration() {
  echo "Verifying database integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "Database integration verification" "python manage.py verify_database_integration --all"; then
    echo "Database integration verification failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "Database integration verification completed successfully" | tee -a "$LOG_FILE"
  return 0
}

SUCCESS=true

if [ "$ALL" = true ] || [ "$SUPABASE" = true ]; then
  if ! test_supabase; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$RAGFLOW" = true ]; then
  if ! test_ragflow; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$DRAGONFLY" = true ]; then
  if ! test_dragonfly; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$ROCKETMQ" = true ]; then
  if ! test_rocketmq; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$DORIS" = true ]; then
  if ! test_doris; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$POSTGRES" = true ]; then
  if ! test_postgres; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$KAFKA" = true ]; then
  if ! test_kafka; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$DJANGO" = true ]; then
  if ! run_django_tests; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$VERIFY" = true ]; then
  if ! verify_database_integration; then
    SUCCESS=false
  fi
fi

echo "" | tee -a "$LOG_FILE"
echo "Database integration tests completed at $(date)" | tee -a "$LOG_FILE"

if [ "$SUCCESS" = true ]; then
  echo "All tests completed successfully" | tee -a "$LOG_FILE"
  exit 0
else
  echo "Some tests failed. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
  exit 1
fi
