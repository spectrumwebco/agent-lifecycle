package config

import (
	"log"
	"net"
	"os"
	"path/filepath"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func GetPostgresOperatorDatabases() map[string]map[string]interface{} {
	if InKubernetes {
		return map[string]map[string]interface{}{
			"agent_runtime": {
				"ENGINE":       "django.db.backends.postgresql",
				"NAME":         "agent_runtime",
				"USER":         "agent_user",
				"PASSWORD":     os.Getenv("POSTGRES_PASSWORD"),
				"HOST":         "agent-postgres-cluster-primary.default.svc.cluster.local",
				"PORT":         "5432",
				"CONN_MAX_AGE": 600,
			},
			"agent_db": {
				"ENGINE":       "django.db.backends.postgresql",
				"NAME":         "agent_db",
				"USER":         "agent_user",
				"PASSWORD":     os.Getenv("POSTGRES_PASSWORD"),
				"HOST":         "agent-postgres-cluster-primary.default.svc.cluster.local",
				"PORT":         "5432",
				"CONN_MAX_AGE": 600,
			},
			"trajectory_db": {
				"ENGINE":       "django.db.backends.postgresql",
				"NAME":         "trajectory_db",
				"USER":         "agent_user",
				"PASSWORD":     os.Getenv("POSTGRES_PASSWORD"),
				"HOST":         "agent-postgres-cluster-primary.default.svc.cluster.local",
				"PORT":         "5432",
				"CONN_MAX_AGE": 600,
			},
			"ml_db": {
				"ENGINE":       "django.db.backends.postgresql",
				"NAME":         "ml_db",
				"USER":         "agent_user",
				"PASSWORD":     os.Getenv("POSTGRES_PASSWORD"),
				"HOST":         "agent-postgres-cluster-primary.default.svc.cluster.local",
				"PORT":         "5432",
				"CONN_MAX_AGE": 600,
			},
		}
	}

	postgresAvailable := false
	conn, err := net.DialTimeout("tcp", "localhost:5432", 1*time.Second)
	if err == nil {
		conn.Close()
		postgresAvailable = true
	} else {
		log.Println("PostgreSQL not available locally, using SQLite for development")
	}

	if postgresAvailable {
		return map[string]map[string]interface{}{
			"agent_runtime": {
				"ENGINE":       "django.db.backends.postgresql",
				"NAME":         "agent_runtime",
				"USER":         "postgres",
				"PASSWORD":     "postgres",
				"HOST":         "localhost",
				"PORT":         "5432",
				"CONN_MAX_AGE": 600,
			},
			"agent_db": {
				"ENGINE":       "django.db.backends.postgresql",
				"NAME":         "agent_db",
				"USER":         "postgres",
				"PASSWORD":     "postgres",
				"HOST":         "localhost",
				"PORT":         "5432",
				"CONN_MAX_AGE": 600,
			},
			"trajectory_db": {
				"ENGINE":       "django.db.backends.postgresql",
				"NAME":         "trajectory_db",
				"USER":         "postgres",
				"PASSWORD":     "postgres",
				"HOST":         "localhost",
				"PORT":         "5432",
				"CONN_MAX_AGE": 600,
			},
			"ml_db": {
				"ENGINE":       "django.db.backends.postgresql",
				"NAME":         "ml_db",
				"USER":         "postgres",
				"PASSWORD":     "postgres",
				"HOST":         "localhost",
				"PORT":         "5432",
				"CONN_MAX_AGE": 600,
			},
		}
	}

	baseDir := filepath.Dir(filepath.Dir(filepath.Dir(filepath.Dir(os.Args[0]))))
	return map[string]map[string]interface{}{
		"agent_runtime": {
			"ENGINE": "django.db.backends.sqlite3",
			"NAME":   filepath.Join(baseDir, "agent_runtime.sqlite3"),
		},
		"agent_db": {
			"ENGINE": "django.db.backends.sqlite3",
			"NAME":   filepath.Join(baseDir, "agent_db.sqlite3"),
		},
		"trajectory_db": {
			"ENGINE": "django.db.backends.sqlite3",
			"NAME":   filepath.Join(baseDir, "trajectory_db.sqlite3"),
		},
		"ml_db": {
			"ENGINE": "django.db.backends.sqlite3",
			"NAME":   filepath.Join(baseDir, "ml_db.sqlite3"),
		},
	}
}

func GetPostgresOperatorDatabaseRouters() []string {
	return []string{"agent_api.database_routers.AgentRuntimeRouter"}
}

func init() {
	core.RegisterConfig("postgres_operator", map[string]interface{}{
		"databases":        GetPostgresOperatorDatabases(),
		"database_routers": GetPostgresOperatorDatabaseRouters(),
	})
}
