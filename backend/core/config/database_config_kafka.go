package config

import (
	"log"
	"net"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

func GetKafkaConfig() map[string]interface{} {
	if InKubernetes {
		return map[string]interface{}{
			"bootstrap_servers":   "kafka-broker.default.svc.cluster.local:9092",
			"client_id":           "agent-runtime",
			"group_id":            "agent-runtime-group",
			"auto_offset_reset":   "earliest",
			"enable_auto_commit":  true,
		}
	}

	kafkaAvailable := false
	conn, err := net.DialTimeout("tcp", "localhost:9092", 1*time.Second)
	if err == nil {
		conn.Close()
		kafkaAvailable = true
	} else {
		log.Println("Apache Kafka not available locally, using mock Kafka for development")
	}

	if kafkaAvailable {
		return map[string]interface{}{
			"bootstrap_servers":   "localhost:9092",
			"client_id":           "agent-runtime",
			"group_id":            "agent-runtime-group",
			"auto_offset_reset":   "earliest",
			"enable_auto_commit":  true,
		}
	}

	return map[string]interface{}{
		"bootstrap_servers":   "localhost:9092",
		"client_id":           "agent-runtime",
		"group_id":            "agent-runtime-group",
		"auto_offset_reset":   "earliest",
		"enable_auto_commit":  true,
		"use_mock":            true,
	}
}

func GetKafkaTopics() map[string]string {
	return map[string]string{
		"agent_events":      "agent-events",
		"agent_commands":    "agent-commands",
		"agent_responses":   "agent-responses",
		"agent_logs":        "agent-logs",
		"trajectory_events": "trajectory-events",
		"ml_events":         "ml-events",
		"ml_commands":       "ml-commands",
		"ml_responses":      "ml-responses",
		"ml_logs":           "ml-logs",
		"shared_state":      "shared-state",
	}
}

func GetKafkaConsumerConfig() map[string]interface{} {
	kafkaConfig := GetKafkaConfig()
	return map[string]interface{}{
		"bootstrap_servers":  kafkaConfig["bootstrap_servers"],
		"group_id":           kafkaConfig["group_id"],
		"auto_offset_reset":  kafkaConfig["auto_offset_reset"],
		"enable_auto_commit": kafkaConfig["enable_auto_commit"],
	}
}

func GetKafkaProducerConfig() map[string]interface{} {
	kafkaConfig := GetKafkaConfig()
	return map[string]interface{}{
		"bootstrap_servers": kafkaConfig["bootstrap_servers"],
		"client_id":         kafkaConfig["client_id"],
	}
}

func init() {
	core.RegisterConfig("kafka", map[string]interface{}{
		"kafka_config":         GetKafkaConfig(),
		"kafka_topics":         GetKafkaTopics(),
		"kafka_consumer_config": GetKafkaConsumerConfig(),
		"kafka_producer_config": GetKafkaProducerConfig(),
	})
}
