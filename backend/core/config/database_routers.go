package config

import (
	"log"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/db"
)

type AgentRuntimeRouter struct{}

func NewAgentRuntimeRouter() *AgentRuntimeRouter {
	return &AgentRuntimeRouter{}
}

func (r *AgentRuntimeRouter) DBForRead(model db.Model, hints map[string]interface{}) string {
	meta := model.GetMeta()
	appLabel := meta.GetAppLabel()

	if appLabel == "python_agent" && meta.HasAttr("agent_model") {
		return "agent_db"
	}

	if appLabel == "python_agent" && meta.HasAttr("trajectory_model") {
		return "trajectory_db"
	}

	if appLabel == "python_agent" && meta.HasAttr("ml_model") {
		return "ml_db"
	}

	if appLabel == "python_agent" && meta.HasAttr("analytics_model") {
		return "default"
	}

	if appLabel == "python_agent" && meta.HasAttr("supabase_db") {
		dbName := meta.GetAttr("supabase_db")
		if dbName != "" {
			return dbName
		}
	}

	if appLabel == "api" || appLabel == "ml_api" || appLabel == "python_agent" || appLabel == "python_ml" || appLabel == "app" {
		return "default"
	}

	return ""
}

func (r *AgentRuntimeRouter) DBForWrite(model db.Model, hints map[string]interface{}) string {
	meta := model.GetMeta()
	appLabel := meta.GetAppLabel()

	if appLabel == "python_agent" && meta.HasAttr("agent_model") {
		return "agent_db"
	}

	if appLabel == "python_agent" && meta.HasAttr("trajectory_model") {
		return "trajectory_db"
	}

	if appLabel == "python_agent" && meta.HasAttr("ml_model") {
		return "ml_db"
	}

	if appLabel == "python_agent" && meta.HasAttr("analytics_model") {
		return "default"
	}

	if appLabel == "python_agent" && meta.HasAttr("supabase_db") {
		dbName := meta.GetAttr("supabase_db")
		if dbName != "" {
			return dbName
		}
	}

	if appLabel == "api" || appLabel == "ml_api" || appLabel == "python_agent" || appLabel == "python_ml" || appLabel == "app" {
		return "default"
	}

	return ""
}

func (r *AgentRuntimeRouter) AllowRelation(obj1, obj2 db.Model, hints map[string]interface{}) bool {
	meta1 := obj1.GetMeta()
	meta2 := obj2.GetMeta()

	if meta1.HasAttr("agent_model") && meta2.HasAttr("agent_model") {
		return true
	}

	if meta1.HasAttr("trajectory_model") && meta2.HasAttr("trajectory_model") {
		return true
	}

	if meta1.HasAttr("ml_model") && meta2.HasAttr("ml_model") {
		return true
	}

	if meta1.HasAttr("analytics_model") && meta2.HasAttr("analytics_model") {
		return true
	}

	if meta1.HasAttr("supabase_db") && meta2.HasAttr("supabase_db") &&
		meta1.GetAttr("supabase_db") == meta2.GetAttr("supabase_db") {
		return true
	}

	if meta1.GetAppLabel() == meta2.GetAppLabel() {
		return true
	}

	return false
}

func (r *AgentRuntimeRouter) AllowMigrate(dbName, appLabel, modelName string, hints map[string]interface{}) bool {
	model, hasModel := hints["model"].(db.Model)

	if dbName == "agent_db" && appLabel == "python_agent" {
		if hasModel && model.GetMeta().HasAttr("agent_model") {
			return true
		} else if modelName != "" && db.StringStartsWith(modelName, "agent") {
			return true
		}
		return false
	}

	if dbName == "trajectory_db" && appLabel == "python_agent" {
		if hasModel && model.GetMeta().HasAttr("trajectory_model") {
			return true
		} else if modelName != "" && db.StringStartsWith(modelName, "trajectory") {
			return true
		}
		return false
	}

	if dbName == "ml_db" && appLabel == "python_agent" {
		if hasModel && model.GetMeta().HasAttr("ml_model") {
			return true
		} else if modelName != "" && db.StringStartsWith(modelName, "ml") {
			return true
		}
		return false
	}

	if dbName == "default" {
		if hasModel && model.GetMeta().HasAttr("analytics_model") {
			return true
		} else if appLabel == "api" || appLabel == "ml_api" || appLabel == "app" {
			return true
		} else if appLabel == "python_agent" && modelName != "" && db.StringStartsWith(modelName, "analytics") {
			return true
		}
	}

	if db.StringStartsWith(dbName, "supabase_") {
		if hasModel && model.GetMeta().HasAttr("supabase_db") && model.GetMeta().GetAttr("supabase_db") == dbName {
			return true
		}
		return false
	}

	return false
}

type AgentRouter struct{}

func NewAgentRouter() *AgentRouter {
	return &AgentRouter{}
}

func (r *AgentRouter) DBForRead(model db.Model, hints map[string]interface{}) string {
	meta := model.GetMeta()
	if meta.GetAppLabel() == "python_agent" && meta.HasAttr("agent_model") {
		log.Println("Warning: Using legacy AgentRouter, please update to AgentRuntimeRouter")
		return "agent_db"
	}
	return ""
}

func (r *AgentRouter) DBForWrite(model db.Model, hints map[string]interface{}) string {
	meta := model.GetMeta()
	if meta.GetAppLabel() == "python_agent" && meta.HasAttr("agent_model") {
		log.Println("Warning: Using legacy AgentRouter, please update to AgentRuntimeRouter")
		return "agent_db"
	}
	return ""
}

func (r *AgentRouter) AllowRelation(obj1, obj2 db.Model, hints map[string]interface{}) bool {
	meta1 := obj1.GetMeta()
	meta2 := obj2.GetMeta()

	if meta1.GetAppLabel() == "python_agent" && meta1.HasAttr("agent_model") &&
		meta2.GetAppLabel() == "python_agent" && meta2.HasAttr("agent_model") {
		return true
	}
	return false
}

func (r *AgentRouter) AllowMigrate(dbName, appLabel, modelName string, hints map[string]interface{}) bool {
	if dbName == "agent_db" && appLabel == "python_agent" {
		model, hasModel := hints["model"].(db.Model)
		if hasModel && model.GetMeta().HasAttr("agent_model") {
			return true
		}
	}
	return false
}

type TrajectoryRouter struct{}

func NewTrajectoryRouter() *TrajectoryRouter {
	return &TrajectoryRouter{}
}

func (r *TrajectoryRouter) DBForRead(model db.Model, hints map[string]interface{}) string {
	meta := model.GetMeta()
	if meta.GetAppLabel() == "python_agent" && meta.HasAttr("trajectory_model") {
		log.Println("Warning: Using legacy TrajectoryRouter, please update to AgentRuntimeRouter")
		return "trajectory_db"
	}
	return ""
}

func (r *TrajectoryRouter) DBForWrite(model db.Model, hints map[string]interface{}) string {
	meta := model.GetMeta()
	if meta.GetAppLabel() == "python_agent" && meta.HasAttr("trajectory_model") {
		log.Println("Warning: Using legacy TrajectoryRouter, please update to AgentRuntimeRouter")
		return "trajectory_db"
	}
	return ""
}

func (r *TrajectoryRouter) AllowRelation(obj1, obj2 db.Model, hints map[string]interface{}) bool {
	meta1 := obj1.GetMeta()
	meta2 := obj2.GetMeta()

	if meta1.GetAppLabel() == "python_agent" && meta1.HasAttr("trajectory_model") &&
		meta2.GetAppLabel() == "python_agent" && meta2.HasAttr("trajectory_model") {
		return true
	}
	return false
}

func (r *TrajectoryRouter) AllowMigrate(dbName, appLabel, modelName string, hints map[string]interface{}) bool {
	if dbName == "trajectory_db" && appLabel == "python_agent" {
		model, hasModel := hints["model"].(db.Model)
		if hasModel && model.GetMeta().HasAttr("trajectory_model") {
			return true
		}
	}
	return false
}

type MLRouter struct{}

func NewMLRouter() *MLRouter {
	return &MLRouter{}
}

func (r *MLRouter) DBForRead(model db.Model, hints map[string]interface{}) string {
	meta := model.GetMeta()
	if meta.GetAppLabel() == "python_agent" && meta.HasAttr("ml_model") {
		log.Println("Warning: Using legacy MLRouter, please update to AgentRuntimeRouter")
		return "ml_db"
	}
	return ""
}

func (r *MLRouter) DBForWrite(model db.Model, hints map[string]interface{}) string {
	meta := model.GetMeta()
	if meta.GetAppLabel() == "python_agent" && meta.HasAttr("ml_model") {
		log.Println("Warning: Using legacy MLRouter, please update to AgentRuntimeRouter")
		return "ml_db"
	}
	return ""
}

func (r *MLRouter) AllowRelation(obj1, obj2 db.Model, hints map[string]interface{}) bool {
	meta1 := obj1.GetMeta()
	meta2 := obj2.GetMeta()

	if meta1.GetAppLabel() == "python_agent" && meta1.HasAttr("ml_model") &&
		meta2.GetAppLabel() == "python_agent" && meta2.HasAttr("ml_model") {
		return true
	}
	return false
}

func (r *MLRouter) AllowMigrate(dbName, appLabel, modelName string, hints map[string]interface{}) bool {
	if dbName == "ml_db" && appLabel == "python_agent" {
		model, hasModel := hints["model"].(db.Model)
		if hasModel && model.GetMeta().HasAttr("ml_model") {
			return true
		}
	}
	return false
}

func RegisterRouters() {
	db.RegisterRouter("AgentRuntimeRouter", NewAgentRuntimeRouter())
	db.RegisterRouter("AgentRouter", NewAgentRouter())
	db.RegisterRouter("TrajectoryRouter", NewTrajectoryRouter())
	db.RegisterRouter("MLRouter", NewMLRouter())
}

func init() {
	RegisterRouters()
}
