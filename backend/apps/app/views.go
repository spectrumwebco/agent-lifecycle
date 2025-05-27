package app

import (
	"net/http"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type UserViewSet struct {
	core.ViewSet
}

func NewUserViewSet() *UserViewSet {
	viewSet := &UserViewSet{
		ViewSet: core.NewViewSet("User"),
	}

	viewSet.SetQuerySet(core.GetQuerySet("User").OrderBy("-date_joined"))
	viewSet.SetSerializerClass("UserSerializer")
	viewSet.SetPermissionClasses([]string{"IsAuthenticated"})

	return viewSet
}

func APIRoot(w http.ResponseWriter, r *http.Request) {
	response := map[string]interface{}{
		"status":  "online",
		"version": "1.0.0",
		"message": "Agent Runtime API is running",
	}

	core.JSONResponse(w, response, http.StatusOK)
}

func ExecuteAgentTask(w http.ResponseWriter, r *http.Request) {
	if !core.IsAuthenticated(r) {
		core.JSONResponse(w, map[string]interface{}{
			"status":  "error",
			"message": "Authentication required",
		}, http.StatusUnauthorized)
		return
	}

	try := func() interface{} {
		response := map[string]interface{}{
			"status":  "accepted",
			"task_id": "placeholder-task-id",
			"message": "Task submitted for execution",
		}
		return response
	}

	catch := func(err error) interface{} {
		response := map[string]interface{}{
			"status":  "error",
			"message": err.Error(),
		}
		return response
	}

	result, err := core.TryCatch(try, catch)
	if err != nil {
		core.JSONResponse(w, result, http.StatusInternalServerError)
	} else {
		core.JSONResponse(w, result, http.StatusAccepted)
	}
}

func init() {
	core.RegisterAPIView("api_root", APIRoot, []string{"GET"}, []string{"AllowAny"})
	core.RegisterAPIView("execute_agent_task", ExecuteAgentTask, []string{"POST"}, []string{"IsAuthenticated"})
	core.RegisterViewSet("UserViewSet", NewUserViewSet())
}
