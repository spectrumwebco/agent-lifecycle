package scripts

import (
	"fmt"
	"os"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

func CheckMariaDBConfig() {
	script := `
import os
import sys
import django
from pathlib import Path

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agent_api.settings")
django.setup()

from django.conf import settings
from agent_api.database_config import DATABASES, REDIS_CONFIG

def check_mariadb_config():
    """Check if MariaDB is properly configured."""
    db_config = DATABASES['default']
    
    print("Database Configuration Check:")
    print(f"Engine: {db_config['ENGINE']}")
    print(f"Name: {db_config['NAME']}")
    print(f"User: {db_config['USER']}")
    print(f"Host: {db_config['HOST']}")
    print(f"Port: {db_config['PORT']}")
    
    if 'OPTIONS' in db_config:
        print("\nDatabase Options:")
        for key, value in db_config['OPTIONS'].items():
            print(f"  {key}: {value}")
    
    if db_config['ENGINE'] == 'django.db.backends.mysql':
        print("\n✅ Using MariaDB/MySQL backend")
    else:
        print("\n❌ Not using MariaDB/MySQL backend")
    
    print("\nRedis Configuration:")
    for key, value in REDIS_CONFIG.items():
        print(f"  {key}: {value}")
    
    print("\nDjango Settings Check:")
    if hasattr(settings, 'DATABASES'):
        engine = settings.DATABASES['default']['ENGINE']
        print(f"Settings Engine: {engine}")
        if engine == 'django.db.backends.mysql':
            print("✅ Django settings using MariaDB/MySQL backend")
        else:
            print("❌ Django settings not using MariaDB/MySQL backend")
    else:
        print("❌ DATABASES not found in Django settings")

check_mariadb_config()
`

	cmd := db.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Printf("Error checking MariaDB configuration: %v\n", err)
		fmt.Println(string(output))
		return
	}

	fmt.Println(string(output))
}

func main() {
	CheckMariaDBConfig()
	os.Exit(0)
}
