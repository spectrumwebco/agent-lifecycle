

cd "$(dirname "$0")"
export DJANGO_SETTINGS_MODULE=agent_api.settings

ALL=false
CONNECTIONS=false
TESTS=false
KAFKA=false
POSTGRES=false
DORIS=false
CROSS=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --all)
      ALL=true
      shift
      ;;
    --connections)
      CONNECTIONS=true
      shift
      ;;
    --tests)
      TESTS=true
      shift
      ;;
    --kafka)
      KAFKA=true
      shift
      ;;
    --postgres)
      POSTGRES=true
      shift
      ;;
    --doris)
      DORIS=true
      shift
      ;;
    --cross)
      CROSS=true
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

if [ "$ALL" = false ] && [ "$CONNECTIONS" = false ] && [ "$TESTS" = false ] && [ "$KAFKA" = false ] && [ "$POSTGRES" = false ] && [ "$DORIS" = false ] && [ "$CROSS" = false ]; then
  ALL=true
fi

LOG_FILE="database_verification.log"
echo "Starting database verification at $(date)" | tee -a "$LOG_FILE"

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

verify_database_connections() {
  echo "Verifying database connections..." | tee -a "$LOG_FILE"
  
  if ! run_command "Django database configuration check for Apache Doris" "python manage.py check --database=default"; then
    echo "Database configuration check failed for Apache Doris" | tee -a "$LOG_FILE"
    return 1
  fi
  
  if ! run_command "Django database configuration check for PostgreSQL" "python manage.py check --database=agent_db"; then
    echo "Database configuration check failed for PostgreSQL" | tee -a "$LOG_FILE"
    return 1
  fi
  
  if ! run_command "Database integration verification" "python manage.py verify_database_integration --all"; then
    echo "Database integration verification failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "All database connections verified successfully" | tee -a "$LOG_FILE"
  return 0
}

run_database_tests() {
  echo "Running database integration tests..." | tee -a "$LOG_FILE"
  
  if ! run_command "Database model tests" "python manage.py test apps.python_agent.tests.test_database_models"; then
    echo "Database model tests failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "All database tests passed successfully" | tee -a "$LOG_FILE"
  return 0
}

verify_kafka_integration() {
  echo "Verifying Kafka integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "Kafka integration verification" "python manage.py verify_database_integration --kafka"; then
    echo "Kafka integration verification failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "Kafka integration verified successfully" | tee -a "$LOG_FILE"
  return 0
}

verify_postgres_integration() {
  echo "Verifying PostgreSQL integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "PostgreSQL integration verification" "python manage.py verify_database_integration --postgres"; then
    echo "PostgreSQL integration verification failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "PostgreSQL integration verified successfully" | tee -a "$LOG_FILE"
  return 0
}

verify_doris_integration() {
  echo "Verifying Apache Doris integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "Apache Doris integration verification" "python manage.py verify_database_integration --doris"; then
    echo "Apache Doris integration verification failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "Apache Doris integration verified successfully" | tee -a "$LOG_FILE"
  return 0
}

verify_cross_database_integration() {
  echo "Verifying cross-database integration..." | tee -a "$LOG_FILE"
  
  if ! run_command "Cross-database integration verification" "python manage.py verify_database_integration --integration"; then
    echo "Cross-database integration verification failed" | tee -a "$LOG_FILE"
    return 1
  fi
  
  echo "Cross-database integration verified successfully" | tee -a "$LOG_FILE"
  return 0
}

SUCCESS=true

if [ "$ALL" = true ] || [ "$CONNECTIONS" = true ]; then
  if ! verify_database_connections; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$TESTS" = true ]; then
  if ! run_database_tests; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$KAFKA" = true ]; then
  if ! verify_kafka_integration; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$POSTGRES" = true ]; then
  if ! verify_postgres_integration; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$DORIS" = true ]; then
  if ! verify_doris_integration; then
    SUCCESS=false
  fi
fi

if [ "$ALL" = true ] || [ "$CROSS" = true ]; then
  if ! verify_cross_database_integration; then
    SUCCESS=false
  fi
fi

if [ "$SUCCESS" = true ]; then
  echo "All database verification tests passed successfully" | tee -a "$LOG_FILE"
  exit 0
else
  echo "Some database verification tests failed" | tee -a "$LOG_FILE"
  exit 1
fi
