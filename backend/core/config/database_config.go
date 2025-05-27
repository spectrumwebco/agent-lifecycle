package config

import (
	"log"
	"net"
	"os"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

const (
	EnvLocal      = "local"
	EnvKubernetes = "kubernetes"
)

var (
	InKubernetes = isRunningInKubernetes()
	
	Env = func() string {
		if InKubernetes {
			return EnvKubernetes
		}
		return EnvLocal
	}()
)

func isRunningInKubernetes() bool {
	_, err := os.Stat("/var/run/secrets/kubernetes.io/serviceaccount/token")
	return err == nil
}

type DatabaseSettings struct {
	Environment string

	DBEngine   string
	DBName     string
	DBUser     string
	DBPassword string
	DBHost     string
	DBPort     int

	AgentDBName     string
	AgentDBUser     string
	AgentDBPassword string
	AgentDBHost     string
	AgentDBPort     int

	TrajectoryDBName     string
	TrajectoryDBUser     string
	TrajectoryDBPassword string
	TrajectoryDBHost     string
	TrajectoryDBPort     int

	MLDBName     string
	MLDBUser     string
	MLDBPassword string
	MLDBHost     string
	MLDBPort     int

	RedisHost     string
	RedisPort     int
	RedisDB       int
	RedisPassword string
	RedisUseSSL   bool

	VectorDBAPIKey      string
	VectorDBEnvironment string
	VectorDBIndexName   string
	VectorDBHost        string
	VectorDBPort        int

	RocketMQHost string
	RocketMQPort int
}

func NewDatabaseSettings() *DatabaseSettings {
	dbHost := "localhost"
	if InKubernetes {
		dbHost = "supabase-db.default.svc.cluster.local"
	}

	redisHost := "localhost"
	if InKubernetes {
		redisHost = "dragonfly-db.default.svc.cluster.local"
	}

	vectorDBHost := "localhost"
	if InKubernetes {
		vectorDBHost = "ragflow.default.svc.cluster.local"
	}

	rocketMQHost := "localhost"
	if InKubernetes {
		rocketMQHost = "rocketmq.default.svc.cluster.local"
	}

	return &DatabaseSettings{
		Environment: Env,

		DBEngine:   "django.db.backends.postgresql",
		DBName:     "postgres",
		DBUser:     "postgres",
		DBPassword: "postgres",
		DBHost:     dbHost,
		DBPort:     5432,

		AgentDBName:     "agent_db",
		AgentDBUser:     "postgres",
		AgentDBPassword: "postgres",
		AgentDBHost:     dbHost,
		AgentDBPort:     5432,

		TrajectoryDBName:     "trajectory_db",
		TrajectoryDBUser:     "postgres",
		TrajectoryDBPassword: "postgres",
		TrajectoryDBHost:     dbHost,
		TrajectoryDBPort:     5432,

		MLDBName:     "ml_db",
		MLDBUser:     "postgres",
		MLDBPassword: "postgres",
		MLDBHost:     dbHost,
		MLDBPort:     5432,

		RedisHost:     redisHost,
		RedisPort:     6379,
		RedisDB:       0,
		RedisPassword: "",
		RedisUseSSL:   false,

		VectorDBAPIKey:      "",
		VectorDBEnvironment: "default",
		VectorDBIndexName:   "agent-docs",
		VectorDBHost:        vectorDBHost,
		VectorDBPort:        8000,

		RocketMQHost: rocketMQHost,
		RocketMQPort: 9876,
	}
}

func (s *DatabaseSettings) LoadFromEnv() {
}

var DBSettings = NewDatabaseSettings()

func IsPostgresAvailable() bool {
	if InKubernetes {
		return true
	}

	conn, err := net.DialTimeout("tcp", "localhost:5432", 1*time.Second)
	if err != nil {
		return false
	}
	conn.Close()
	return true
}

func GetDatabases() map[string]map[string]interface{} {
	if Env == EnvLocal && !IsPostgresAvailable() {
		log.Println("PostgreSQL not available locally, using MariaDB for development")
		return map[string]map[string]interface{}{
			"default": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "agent_runtime",
				"USER":     "agent_user",
				"PASSWORD": "agent_password",
				"HOST":     "localhost",
				"PORT":     "3306",
				"OPTIONS": map[string]interface{}{
					"charset":      "utf8mb4",
					"init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
				},
			},
			"agent_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "agent_db",
				"USER":     "agent_user",
				"PASSWORD": "agent_password",
				"HOST":     "localhost",
				"PORT":     "3306",
				"OPTIONS": map[string]interface{}{
					"charset":      "utf8mb4",
					"init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
				},
			},
			"trajectory_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "trajectory_db",
				"USER":     "agent_user",
				"PASSWORD": "agent_password",
				"HOST":     "localhost",
				"PORT":     "3306",
				"OPTIONS": map[string]interface{}{
					"charset":      "utf8mb4",
					"init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
				},
			},
			"ml_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "ml_db",
				"USER":     "agent_user",
				"PASSWORD": "agent_password",
				"HOST":     "localhost",
				"PORT":     "3306",
				"OPTIONS": map[string]interface{}{
					"charset":      "utf8mb4",
					"init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
				},
			},
		}
	}

	return map[string]map[string]interface{}{
		"default": {
			"ENGINE":   DBSettings.DBEngine,
			"NAME":     DBSettings.DBName,
			"USER":     DBSettings.DBUser,
			"PASSWORD": DBSettings.DBPassword,
			"HOST":     DBSettings.DBHost,
			"PORT":     DBSettings.DBPort,
			"OPTIONS": map[string]interface{}{
				"sslmode": "prefer", // Use 'require' in production
			},
		},
		"agent_db": {
			"ENGINE":   DBSettings.DBEngine,
			"NAME":     DBSettings.AgentDBName,
			"USER":     DBSettings.AgentDBUser,
			"PASSWORD": DBSettings.AgentDBPassword,
			"HOST":     DBSettings.AgentDBHost,
			"PORT":     DBSettings.AgentDBPort,
			"OPTIONS": map[string]interface{}{
				"sslmode": "prefer", // Use 'require' in production
			},
		},
		"trajectory_db": {
			"ENGINE":   DBSettings.DBEngine,
			"NAME":     DBSettings.TrajectoryDBName,
			"USER":     DBSettings.TrajectoryDBUser,
			"PASSWORD": DBSettings.TrajectoryDBPassword,
			"HOST":     DBSettings.TrajectoryDBHost,
			"PORT":     DBSettings.TrajectoryDBPort,
			"OPTIONS": map[string]interface{}{
				"sslmode": "prefer", // Use 'require' in production
			},
		},
		"ml_db": {
			"ENGINE":   DBSettings.DBEngine,
			"NAME":     DBSettings.MLDBName,
			"USER":     DBSettings.MLDBUser,
			"PASSWORD": DBSettings.MLDBPassword,
			"HOST":     DBSettings.MLDBHost,
			"PORT":     DBSettings.MLDBPort,
			"OPTIONS": map[string]interface{}{
				"sslmode": "prefer", // Use 'require' in production
			},
		},
	}
}

func GetDatabaseRouters() []string {
	return []string{
		"agent_api.database_routers.AgentRouter",
		"agent_api.database_routers.TrajectoryRouter",
		"agent_api.database_routers.MLRouter",
	}
}

func GetRedisConfig() map[string]interface{} {
	return map[string]interface{}{
		"host":     DBSettings.RedisHost,
		"port":     DBSettings.RedisPort,
		"db":       DBSettings.RedisDB,
		"password": DBSettings.RedisPassword,
		"ssl":      DBSettings.RedisUseSSL,
	}
}

func GetVectorDBConfig() map[string]interface{} {
	return map[string]interface{}{
		"api_key":     DBSettings.VectorDBAPIKey,
		"environment": DBSettings.VectorDBEnvironment,
		"index_name":  DBSettings.VectorDBIndexName,
		"host":        DBSettings.VectorDBHost,
		"port":        DBSettings.VectorDBPort,
	}
}

func GetRocketMQConfig() map[string]interface{} {
	return map[string]interface{}{
		"host": DBSettings.RocketMQHost,
		"port": DBSettings.RocketMQPort,
	}
}

func init() {
	core.RegisterConfig("database", map[string]interface{}{
		"databases":        GetDatabases(),
		"database_routers": GetDatabaseRouters(),
		"redis":            GetRedisConfig(),
		"vector_db":        GetVectorDBConfig(),
		"rocketmq":         GetRocketMQConfig(),
	})
}
