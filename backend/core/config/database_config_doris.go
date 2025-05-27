package config

import (
	"log"
	"net"
	"os"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func GetDorisDatabases() map[string]map[string]interface{} {
	if InKubernetes {
		return map[string]map[string]interface{}{
			"default": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "agent_runtime",
				"USER":     "root",
				"PASSWORD": "", // Will be replaced by Vault
				"HOST":     "doris-fe.default.svc.cluster.local",
				"PORT":     "9030",
				"OPTIONS": map[string]interface{}{
					"charset":     "utf8mb4",
					"use_unicode": true,
				},
			},
			"agent_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "agent_db",
				"USER":     "root",
				"PASSWORD": "", // Will be replaced by Vault
				"HOST":     "doris-fe.default.svc.cluster.local",
				"PORT":     "9030",
				"OPTIONS": map[string]interface{}{
					"charset":     "utf8mb4",
					"use_unicode": true,
				},
			},
			"trajectory_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "trajectory_db",
				"USER":     "root",
				"PASSWORD": "", // Will be replaced by Vault
				"HOST":     "doris-fe.default.svc.cluster.local",
				"PORT":     "9030",
				"OPTIONS": map[string]interface{}{
					"charset":     "utf8mb4",
					"use_unicode": true,
				},
			},
			"ml_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "ml_db",
				"USER":     "root",
				"PASSWORD": "", // Will be replaced by Vault
				"HOST":     "doris-fe.default.svc.cluster.local",
				"PORT":     "9030",
				"OPTIONS": map[string]interface{}{
					"charset":     "utf8mb4",
					"use_unicode": true,
				},
			},
		}
	}

	dorisAvailable := false
	conn, err := net.DialTimeout("tcp", "localhost:9030", 1*time.Second)
	if err == nil {
		conn.Close()
		dorisAvailable = true
	} else {
		log.Println("Apache Doris not available locally, using MariaDB for development")
	}

	if dorisAvailable {
		return map[string]map[string]interface{}{
			"default": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "agent_runtime",
				"USER":     "root",
				"PASSWORD": "",
				"HOST":     "localhost",
				"PORT":     "9030",
				"OPTIONS": map[string]interface{}{
					"charset":     "utf8mb4",
					"use_unicode": true,
				},
			},
			"agent_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "agent_db",
				"USER":     "root",
				"PASSWORD": "",
				"HOST":     "localhost",
				"PORT":     "9030",
				"OPTIONS": map[string]interface{}{
					"charset":     "utf8mb4",
					"use_unicode": true,
				},
			},
			"trajectory_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "trajectory_db",
				"USER":     "root",
				"PASSWORD": "",
				"HOST":     "localhost",
				"PORT":     "9030",
				"OPTIONS": map[string]interface{}{
					"charset":     "utf8mb4",
					"use_unicode": true,
				},
			},
			"ml_db": {
				"ENGINE":   "django.db.backends.mysql",
				"NAME":     "ml_db",
				"USER":     "root",
				"PASSWORD": "",
				"HOST":     "localhost",
				"PORT":     "9030",
				"OPTIONS": map[string]interface{}{
					"charset":     "utf8mb4",
					"use_unicode": true,
				},
			},
		}
	}

	return map[string]map[string]interface{}{
		"default": {
			"ENGINE":   "django.db.backends.mysql",
			"NAME":     "agent_runtime",
			"USER":     "agent_user",
			"PASSWORD": "agent_password",
			"HOST":     "localhost",
			"PORT":     "3306",
			"OPTIONS": map[string]interface{}{
				"charset":     "utf8mb4",
				"use_unicode": true,
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
				"charset":     "utf8mb4",
				"use_unicode": true,
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
				"charset":     "utf8mb4",
				"use_unicode": true,
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
				"charset":     "utf8mb4",
				"use_unicode": true,
			},
		},
	}
}

func GetDorisDatabaseRouters() []string {
	return []string{"agent_api.database_routers.AgentDatabaseRouter"}
}

func GetDorisRedisConfig() map[string]interface{} {
	if InKubernetes {
		return map[string]interface{}{
			"host":     "dragonfly-db.default.svc.cluster.local",
			"port":     6379,
			"db":       0,
			"password": "", // Will be replaced by Vault
		}
	}

	redisAvailable := false
	conn, err := net.DialTimeout("tcp", "localhost:6379", 1*time.Second)
	if err == nil {
		conn.Close()
		redisAvailable = true
	} else {
		log.Println("Redis not available locally, using in-memory cache for development")
	}

	if redisAvailable {
		return map[string]interface{}{
			"host":     "localhost",
			"port":     6379,
			"db":       0,
			"password": "",
		}
	}

	return map[string]interface{}{
		"host":       "localhost",
		"port":       6379,
		"db":         0,
		"password":   "",
		"local_only": true,
	}
}

func GetDorisVectorDBConfig() map[string]interface{} {
	if InKubernetes {
		return map[string]interface{}{
			"host":    "ragflow.default.svc.cluster.local",
			"port":    8000,
			"api_key": "", // Will be replaced by Vault
		}
	}

	ragflowAvailable := false
	conn, err := net.DialTimeout("tcp", "localhost:8000", 1*time.Second)
	if err == nil {
		conn.Close()
		ragflowAvailable = true
	} else {
		log.Println("RAGflow not available locally, using mock vector database for development")
	}

	if ragflowAvailable {
		return map[string]interface{}{
			"host":    "localhost",
			"port":    8000,
			"api_key": "",
		}
	}

	return map[string]interface{}{
		"host":       "localhost",
		"port":       8000,
		"api_key":    "",
		"local_only": true,
	}
}

func GetDorisRocketMQConfig() map[string]interface{} {
	if InKubernetes {
		return map[string]interface{}{
			"host":       "rocketmq.default.svc.cluster.local",
			"port":       9876,
			"access_key": "", // Will be replaced by Vault
			"secret_key": "", // Will be replaced by Vault
		}
	}

	rocketmqAvailable := false
	conn, err := net.DialTimeout("tcp", "localhost:9876", 1*time.Second)
	if err == nil {
		conn.Close()
		rocketmqAvailable = true
	} else {
		log.Println("RocketMQ not available locally, using mock messaging for development")
	}

	if rocketmqAvailable {
		return map[string]interface{}{
			"host":       "localhost",
			"port":       9876,
			"access_key": "",
			"secret_key": "",
		}
	}

	return map[string]interface{}{
		"host":       "localhost",
		"port":       9876,
		"access_key": "",
		"secret_key": "",
		"local_only": true,
	}
}

func GetDorisConfig() map[string]interface{} {
	host := "localhost"
	if InKubernetes {
		host = "doris-fe.default.svc.cluster.local"
	}

	return map[string]interface{}{
		"host":      host,
		"http_port": 8030,
		"query_port": 9030,
		"username":  "root",
		"password":  "", // Will be replaced by Vault
		"database":  "agent_runtime",
	}
}

func init() {
	core.RegisterConfig("doris", map[string]interface{}{
		"databases":        GetDorisDatabases(),
		"database_routers": GetDorisDatabaseRouters(),
		"redis":            GetDorisRedisConfig(),
		"vector_db":        GetDorisVectorDBConfig(),
		"rocketmq":         GetDorisRocketMQConfig(),
		"doris":            GetDorisConfig(),
	})
}
