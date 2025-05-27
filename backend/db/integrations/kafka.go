package integrations

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var logger = log.New(os.Stdout, "kafka: ", log.LstdFlags)

type KafkaClient struct {
	BootstrapServers string
	ClientID string
	GroupID string
	TopicPrefix string
	producer *kafka.Producer
	consumer *kafka.Consumer
}

func NewKafkaClient(bootstrapServers, clientID, groupID string) *KafkaClient {
	kafkaConfig := db.GetSettingMap("KAFKA_CONFIG")
	
	if bootstrapServers == "" {
		bootstrapServers = kafkaConfig["bootstrap_servers"]
		if bootstrapServers == "" {
			bootstrapServers = "localhost:9092"
		}
	}
	
	if clientID == "" {
		clientID = fmt.Sprintf("django-kafka-%p", &KafkaClient{})
	}
	
	if groupID == "" {
		groupID = fmt.Sprintf("django-kafka-group-%p", &KafkaClient{})
	}
	
	topicPrefix := kafkaConfig["topic_prefix"]
	
	return &KafkaClient{
		BootstrapServers: bootstrapServers,
		ClientID:         clientID,
		GroupID:          groupID,
		TopicPrefix:      topicPrefix,
	}
}

func (c *KafkaClient) GetProducer() (*kafka.Producer, error) {
	if c.producer == nil {
		var err error
		c.producer, err = kafka.NewProducer(&kafka.ConfigMap{
			"bootstrap.servers": c.BootstrapServers,
			"client.id":         c.ClientID,
		})
		if err != nil {
			return nil, fmt.Errorf("failed to create producer: %v", err)
		}
		
		go func() {
			for e := range c.producer.Events() {
				switch ev := e.(type) {
				case *kafka.Message:
					if ev.TopicPartition.Error != nil {
						logger.Printf("Delivery failed: %v\n", ev.TopicPartition.Error)
					} else {
						logger.Printf("Delivered message to %v\n", ev.TopicPartition)
					}
				}
			}
		}()
	}
	
	return c.producer, nil
}

func (c *KafkaClient) GetConsumer(topics []string, groupID string, autoOffsetReset string) (*kafka.Consumer, error) {
	if autoOffsetReset == "" {
		autoOffsetReset = "earliest"
	}
	
	if groupID == "" {
		groupID = c.GroupID
	}
	
	consumer, err := kafka.NewConsumer(&kafka.ConfigMap{
		"bootstrap.servers": c.BootstrapServers,
		"group.id":          groupID,
		"auto.offset.reset": autoOffsetReset,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create consumer: %v", err)
	}
	
	if len(topics) > 0 {
		fullTopics := make([]string, len(topics))
		for i, topic := range topics {
			fullTopics[i] = c.GetFullTopicName(topic)
		}
		
		err = consumer.SubscribeTopics(fullTopics, nil)
		if err != nil {
			consumer.Close()
			return nil, fmt.Errorf("failed to subscribe to topics: %v", err)
		}
	}
	
	return consumer, nil
}

func (c *KafkaClient) GetFullTopicName(topic string) string {
	if c.TopicPrefix != "" {
		return fmt.Sprintf("%s.%s", c.TopicPrefix, topic)
	}
	return topic
}

func (c *KafkaClient) Produce(topic string, value interface{}, key string, headers []kafka.Header, callback func(*kafka.Message, error)) error {
	producer, err := c.GetProducer()
	if err != nil {
		return err
	}
	
	fullTopic := c.GetFullTopicName(topic)
	
	var valueBytes []byte
	switch v := value.(type) {
	case []byte:
		valueBytes = v
	case string:
		valueBytes = []byte(v)
	default:
		jsonBytes, err := json.Marshal(value)
		if err != nil {
			return fmt.Errorf("failed to marshal value to JSON: %v", err)
		}
		valueBytes = jsonBytes
	}
	
	var keyBytes []byte
	if key != "" {
		keyBytes = []byte(key)
	}
	
	message := &kafka.Message{
		TopicPartition: kafka.TopicPartition{
			Topic:     &fullTopic,
			Partition: kafka.PartitionAny,
		},
		Value:   valueBytes,
		Key:     keyBytes,
		Headers: headers,
	}
	
	err = producer.Produce(message, nil)
	if err != nil {
		return fmt.Errorf("failed to produce message: %v", err)
	}
	
	producer.Poll(0)
	
	return nil
}

func (c *KafkaClient) Flush(timeoutMs int) int {
	if c.producer == nil {
		return 0
	}
	
	return c.producer.Flush(timeoutMs)
}

func (c *KafkaClient) Consume(topics []string, timeoutMs int, numMessages int, groupID string) ([]map[string]interface{}, error) {
	consumer, err := c.GetConsumer(topics, groupID, "")
	if err != nil {
		return nil, err
	}
	defer consumer.Close()
	
	messages := make([]map[string]interface{}, 0, numMessages)
	timeout := time.Duration(timeoutMs) * time.Millisecond
	
	for i := 0; i < numMessages; i++ {
		msg, err := consumer.ReadMessage(timeout)
		if err != nil {
			if err.(kafka.Error).Code() == kafka.ErrTimedOut {
				break
			}
			
			if err.(kafka.Error).Code() == kafka.ErrPartitionEOF {
				logger.Printf("Reached end of partition for topic %s\n", *msg.TopicPartition.Topic)
				continue
			}
			
			logger.Printf("Error consuming from Kafka: %v\n", err)
			continue
		}
		
		var value interface{} = msg.Value
		var jsonValue interface{}
		if err := json.Unmarshal(msg.Value, &jsonValue); err == nil {
			value = jsonValue
		}
		
		headers := make(map[string]string)
		for _, header := range msg.Headers {
			headers[header.Key] = string(header.Value)
		}
		
		message := map[string]interface{}{
			"topic":     *msg.TopicPartition.Topic,
			"partition": msg.TopicPartition.Partition,
			"offset":    msg.TopicPartition.Offset,
			"key":       string(msg.Key),
			"value":     value,
			"headers":   headers,
			"timestamp": msg.Timestamp,
		}
		
		messages = append(messages, message)
	}
	
	return messages, nil
}

func (c *KafkaClient) ConsumeLoop(topics []string, callback func(map[string]interface{}), groupID string, timeoutMs int, exitCondition func() bool) error {
	consumer, err := c.GetConsumer(topics, groupID, "")
	if err != nil {
		return err
	}
	defer consumer.Close()
	
	timeout := time.Duration(timeoutMs) * time.Millisecond
	
	for {
		if exitCondition != nil && exitCondition() {
			break
		}
		
		msg, err := consumer.ReadMessage(timeout)
		if err != nil {
			if err.(kafka.Error).Code() == kafka.ErrTimedOut {
				continue
			}
			
			if err.(kafka.Error).Code() == kafka.ErrPartitionEOF {
				logger.Printf("Reached end of partition for topic %s\n", *msg.TopicPartition.Topic)
				continue
			}
			
			logger.Printf("Error consuming from Kafka: %v\n", err)
			continue
		}
		
		var value interface{} = msg.Value
		var jsonValue interface{}
		if err := json.Unmarshal(msg.Value, &jsonValue); err == nil {
			value = jsonValue
		}
		
		headers := make(map[string]string)
		for _, header := range msg.Headers {
			headers[header.Key] = string(header.Value)
		}
		
		message := map[string]interface{}{
			"topic":     *msg.TopicPartition.Topic,
			"partition": msg.TopicPartition.Partition,
			"offset":    msg.TopicPartition.Offset,
			"key":       string(msg.Key),
			"value":     value,
			"headers":   headers,
			"timestamp": msg.Timestamp,
		}
		
		callback(message)
		
		consumer.CommitMessage(msg)
	}
	
	return nil
}

func (c *KafkaClient) CreateTopic(topic string, numPartitions int, replicationFactor int) (bool, error) {
	fullTopic := c.GetFullTopicName(topic)
	
	adminClient, err := kafka.NewAdminClient(&kafka.ConfigMap{
		"bootstrap.servers": c.BootstrapServers,
	})
	if err != nil {
		return false, fmt.Errorf("failed to create admin client: %v", err)
	}
	defer adminClient.Close()
	
	topicSpec := kafka.TopicSpecification{
		Topic:             fullTopic,
		NumPartitions:     numPartitions,
		ReplicationFactor: replicationFactor,
	}
	
	results, err := adminClient.CreateTopics(context.Background(), []kafka.TopicSpecification{topicSpec})
	if err != nil {
		return false, fmt.Errorf("failed to create topic: %v", err)
	}
	
	for _, result := range results {
		if result.Topic == fullTopic {
			if result.Error.Code() != kafka.ErrNoError {
				logger.Printf("Error creating topic %s: %v\n", fullTopic, result.Error)
				return false, result.Error
			}
			return true, nil
		}
	}
	
	return false, fmt.Errorf("topic creation result not found")
}

func (c *KafkaClient) DeleteTopic(topic string) (bool, error) {
	fullTopic := c.GetFullTopicName(topic)
	
	adminClient, err := kafka.NewAdminClient(&kafka.ConfigMap{
		"bootstrap.servers": c.BootstrapServers,
	})
	if err != nil {
		return false, fmt.Errorf("failed to create admin client: %v", err)
	}
	defer adminClient.Close()
	
	results, err := adminClient.DeleteTopics(context.Background(), []string{fullTopic})
	if err != nil {
		return false, fmt.Errorf("failed to delete topic: %v", err)
	}
	
	for _, result := range results {
		if result.Topic == fullTopic {
			if result.Error.Code() != kafka.ErrNoError {
				logger.Printf("Error deleting topic %s: %v\n", fullTopic, result.Error)
				return false, result.Error
			}
			return true, nil
		}
	}
	
	return false, fmt.Errorf("topic deletion result not found")
}

func (c *KafkaClient) ListTopics() (map[string]interface{}, error) {
	adminClient, err := kafka.NewAdminClient(&kafka.ConfigMap{
		"bootstrap.servers": c.BootstrapServers,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to create admin client: %v", err)
	}
	defer adminClient.Close()
	
	metadata, err := adminClient.GetMetadata(nil, true, 30000)
	if err != nil {
		return nil, fmt.Errorf("failed to list topics: %v", err)
	}
	
	topics := make(map[string]interface{})
	for topic, topicMetadata := range metadata.Topics {
		partitions := make(map[string]interface{})
		for partition, partitionMetadata := range topicMetadata.Partitions {
			partitions[fmt.Sprintf("%d", partition)] = map[string]interface{}{
				"id":       partition,
				"leader":   partitionMetadata.Leader,
				"replicas": partitionMetadata.Replicas,
				"isrs":     partitionMetadata.Isrs,
			}
		}
		
		topics[topic] = map[string]interface{}{
			"topic":      topic,
			"partitions": partitions,
		}
	}
	
	return topics, nil
}

func (c *KafkaClient) Close() {
	if c.producer != nil {
		c.producer.Flush(1000)
		c.producer.Close()
		c.producer = nil
	}
	
	if c.consumer != nil {
		c.consumer.Close()
		c.consumer = nil
	}
}

func GetKafkaClient(bootstrapServers, clientID, groupID string) *KafkaClient {
	return NewKafkaClient(bootstrapServers, clientID, groupID)
}

func ExecutePythonKafkaMethod(methodName string, args ...interface{}) (interface{}, error) {
	argsJSON, err := json.Marshal(args)
	if err != nil {
		return nil, fmt.Errorf("error marshaling args: %v", err)
	}
	
	script := fmt.Sprintf(`
import os
import django
import json
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_api.settings')
django.setup()

from backend.db.integrations.kafka import KafkaClient

client = KafkaClient()
method = getattr(client, '%s', None)
if not method:
    print(json.dumps({'error': 'Method not found'}))
    sys.exit(1)

args = json.loads('%s')
result = method(*args)
print(json.dumps({'result': result}))
`, methodName, strings.Replace(string(argsJSON), "'", "\\'", -1))
	
	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("error executing Python Kafka method: %v", err)
	}
	
	var result struct {
		Result interface{} `json:"result"`
		Error  string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return nil, fmt.Errorf("error unmarshaling result: %v", err)
	}
	
	if result.Error != "" {
		return nil, fmt.Errorf("Python Kafka error: %s", result.Error)
	}
	
	return result.Result, nil
}
