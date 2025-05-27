package db

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

var logger = log.New(os.Stdout, "kled.database.routers: ", log.LstdFlags)

type MultiDatabaseRouter struct{}

func (r *MultiDatabaseRouter) DBForRead(model db.Model, hints map[string]interface{}) string {
	if database := model.GetAttribute("database"); database != "" {
		return database
	}

	appLabel := model.GetAppLabel()
	if appLabel != "" {
		appDBMap := db.GetSettingMap("DATABASE_APPS_MAPPING")
		if db, ok := appDBMap[appLabel]; ok {
			return db
		}
	}

	return "default"
}

func (r *MultiDatabaseRouter) DBForWrite(model db.Model, hints map[string]interface{}) string {
	if database := model.GetAttribute("database"); database != "" {
		return database
	}

	appLabel := model.GetAppLabel()
	if appLabel != "" {
		appDBMap := db.GetSettingMap("DATABASE_APPS_MAPPING")
		if db, ok := appDBMap[appLabel]; ok {
			return db
		}
	}

	return "default"
}

func (r *MultiDatabaseRouter) AllowRelation(obj1, obj2 db.Model, hints map[string]interface{}) bool {
	db1 := r.DBForRead(obj1, nil)
	db2 := r.DBForRead(obj2, nil)

	if db1 == db2 {
		return true
	}

	if db1 == "default" || db2 == "default" {
		return true
	}

	return false
}

func (r *MultiDatabaseRouter) AllowMigrate(database, appLabel string, modelName string, hints map[string]interface{}) bool {
	appDBMap := db.GetSettingMap("DATABASE_APPS_MAPPING")
	
	if db, ok := appDBMap[appLabel]; ok {
		return db == database
	}

	return database == "default"
}

type SupabaseRouter struct{}

func (r *SupabaseRouter) DBForRead(model db.Model, hints map[string]interface{}) string {
	if database := model.GetAttribute("database"); database == "supabase" {
		return "supabase"
	}

	return ""
}

func (r *SupabaseRouter) DBForWrite(model db.Model, hints map[string]interface{}) string {
	if database := model.GetAttribute("database"); database == "supabase" {
		return "supabase"
	}

	return ""
}

func (r *SupabaseRouter) AllowRelation(obj1, obj2 db.Model, hints map[string]interface{}) bool {
	db1 := obj1.GetAttribute("database")
	db2 := obj2.GetAttribute("database")

	if db1 == "supabase" && db2 == "supabase" {
		return true
	}

	if db1 == "supabase" && (db2 == "" || db2 == "default") {
		return true
	}

	if db2 == "supabase" && (db1 == "" || db1 == "default") {
		return true
	}

	return false
}

func (r *SupabaseRouter) AllowMigrate(database, appLabel string, modelName string, hints map[string]interface{}) bool {
	if database == "supabase" {
		if modelName != "" {
			model, ok := hints["model"].(db.Model)
			if ok && model.GetAttribute("database") == "supabase" {
				return true
			}
			return false
		}

		appDBMap := db.GetSettingMap("DATABASE_APPS_MAPPING")
		if db, ok := appDBMap[appLabel]; ok && db == "supabase" {
			return true
		}

		return false
	}

	return false
}

type RAGflowRouter struct{}

func (r *RAGflowRouter) DBForRead(model db.Model, hints map[string]interface{}) string {
	if database := model.GetAttribute("database"); database == "ragflow" {
		return "ragflow"
	}

	return ""
}

func (r *RAGflowRouter) DBForWrite(model db.Model, hints map[string]interface{}) string {
	if database := model.GetAttribute("database"); database == "ragflow" {
		return "ragflow"
	}

	return ""
}

func (r *RAGflowRouter) AllowRelation(obj1, obj2 db.Model, hints map[string]interface{}) bool {
	db1 := obj1.GetAttribute("database")
	db2 := obj2.GetAttribute("database")

	if db1 == "ragflow" && db2 == "ragflow" {
		return true
	}

	if db1 == "ragflow" && (db2 == "" || db2 == "default") {
		return true
	}

	if db2 == "ragflow" && (db1 == "" || db1 == "default") {
		return true
	}

	return false
}

func (r *RAGflowRouter) AllowMigrate(database, appLabel string, modelName string, hints map[string]interface{}) bool {
	if database == "ragflow" {
		return false
	}

	if modelName != "" {
		model, ok := hints["model"].(db.Model)
		if ok && model.GetAttribute("database") == "ragflow" {
			return false
		}
	}

	return false
}

func GetDjangoRouter(routerName string) string {
	script := fmt.Sprintf(`
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_api.settings')
django.setup()

from backend.db.database_routers import MultiDatabaseRouter, SupabaseRouter, RAGflowRouter

routers = {
    'MultiDatabaseRouter': MultiDatabaseRouter,
    'SupabaseRouter': SupabaseRouter,
    'RAGflowRouter': RAGflowRouter,
}

router = routers.get('%s')
if router:
    print(router.__name__)
else:
    print('')
`, routerName)

	cmd := exec.Command("python", "-c", script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		logger.Printf("Error getting Django router: %v", err)
		return ""
	}

	return strings.TrimSpace(string(output))
}

func ExecuteDjangoRouterMethod(routerName, methodName string, args ...interface{}) (string, error) {
	argsJSON, err := json.Marshal(args)
	if err != nil {
		return "", fmt.Errorf("error marshaling args: %v", err)
	}

	script := fmt.Sprintf(`
import os
import django
import json
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_api.settings')
django.setup()

from backend.db.database_routers import MultiDatabaseRouter, SupabaseRouter, RAGflowRouter

routers = {
    'MultiDatabaseRouter': MultiDatabaseRouter(),
    'SupabaseRouter': SupabaseRouter(),
    'RAGflowRouter': RAGflowRouter(),
}

router = routers.get('%s')
if not router:
    print(json.dumps({'error': 'Router not found'}))
    sys.exit(1)

method = getattr(router, '%s', None)
if not method:
    print(json.dumps({'error': 'Method not found'}))
    sys.exit(1)

args = json.loads('%s')
result = method(*args)
print(json.dumps({'result': result}))
`, routerName, methodName, string(argsJSON))

	cmd := exec.Command("python", "-c", script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("error executing Django router method: %v", err)
	}

	var result struct {
		Result interface{} `json:"result"`
		Error  string      `json:"error"`
	}
	if err := json.Unmarshal(output, &result); err != nil {
		return "", fmt.Errorf("error unmarshaling result: %v", err)
	}

	if result.Error != "" {
		return "", fmt.Errorf("Django router error: %s", result.Error)
	}

	resultStr := fmt.Sprintf("%v", result.Result)
	return resultStr, nil
}
