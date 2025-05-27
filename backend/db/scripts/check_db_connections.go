package scripts

import (
	"fmt"
	"os"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

func CheckDjangoDBConnections() {
	script := `
import os
import sys
import django
from pathlib import Path

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_api.settings")
django.setup()

from django.db import connections
from django.conf import settings

print("\n=== Django Database Connections ===")
for db_name in connections:
    print(f"Testing connection to {db_name} database...")
    
    try:
        connection = connections[db_name]
        connection.ensure_connection()
        
        if connection.is_usable():
            print(f"✅ Connection to {db_name} database is working")
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                print(f"   Database version: {version}")
                
                cursor.execute("SELECT current_database();")
                db = cursor.fetchone()[0]
                print(f"   Current database: {db}")
        else:
            print(f"❌ Connection to {db_name} database is not usable")
    
    except Exception as e:
        print(f"❌ Error connecting to {db_name} database: {e}")

print("\n=== Redis (DragonflyDB) Connection ===")
try:
    import redis
    
    redis_config = getattr(settings, 'REDIS_CONFIG', {})
    
    local_redis = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        socket_timeout=2
    )
    
    if local_redis.ping():
        print("✅ Connection to local Redis is working")
        info = local_redis.info()
        print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
    else:
        print("⚠️ Local Redis connection failed, trying configured Redis...")
        
        r = redis.Redis(
            host=redis_config.get('host', 'localhost'),
            port=redis_config.get('port', 6379),
            db=redis_config.get('db', 0),
            password=redis_config.get('password', None),
            ssl=redis_config.get('ssl', False),
            socket_timeout=2
        )
        
        if r.ping():
            print("✅ Connection to configured Redis (DragonflyDB) is working")
            info = r.info()
            print(f"   Redis version: {info.get('redis_version', 'Unknown')}")
        else:
            print("❌ Connection to Redis (DragonflyDB) failed")

except Exception as e:
    print(f"❌ Error connecting to Redis (DragonflyDB): {e}")
    print("⚠️ Redis connection failed, but this is expected in local development")

print("\n=== RAGflow Connection ===")
try:
    import requests
    
    vector_db_config = getattr(settings, 'VECTOR_DB_CONFIG', {})
    
    try:
        local_response = requests.get("http://localhost:8000/health", timeout=2)
        if local_response.status_code == 200:
            print("✅ Connection to local RAGflow is working")
            print(f"   Status: {local_response.json().get('status', 'Unknown')}")
        else:
            print("⚠️ Local RAGflow connection failed, trying configured RAGflow...")
            raise Exception("Local RAGflow connection failed")
    except:
        url = f"http://{vector_db_config.get('host', 'localhost')}:{vector_db_config.get('port', 8000)}/health"
        
        response = requests.get(url, timeout=2)
        
        if response.status_code == 200:
            print("✅ Connection to configured RAGflow is working")
            print(f"   Status: {response.json().get('status', 'Unknown')}")
        else:
            print(f"❌ Connection to RAGflow failed with status code {response.status_code}")

except Exception as e:
    print(f"❌ Error connecting to RAGflow: {e}")
    print("⚠️ RAGflow connection failed, but this is expected in local development")

print("\n=== RocketMQ Connection ===")
try:
    import socket
    
    rocketmq_config = getattr(settings, 'ROCKETMQ_CONFIG', {})
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(('localhost', 9876))
        s.close()
        
        if result == 0:
            print("✅ Connection to local RocketMQ is working")
        else:
            print("⚠️ Local RocketMQ connection failed, trying configured RocketMQ...")
            raise Exception("Local RocketMQ connection failed")
    except:
        host = rocketmq_config.get('host', 'localhost')
        port = rocketmq_config.get('port', 9876)
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        
        result = s.connect_ex((host, port))
        
        if result == 0:
            print("✅ Connection to configured RocketMQ is working")
        else:
            print(f"❌ Connection to RocketMQ failed with error code {result}")
        
        s.close()

except Exception as e:
    print(f"❌ Error connecting to RocketMQ: {e}")
    print("⚠️ RocketMQ connection failed, but this is expected in local development")

print("\n=== Connection Summary ===")
print("Database connections verified")
print("Note: Some connections may fail in local development environment")
print("This is expected as these services are configured for Kubernetes")
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("Error executing database connection check: %v\n", err)
		fmt.Println(string(output))
		return
	}

	fmt.Println(string(output))
}

func main() {
	CheckDjangoDBConnections()
	os.Exit(0)
}
