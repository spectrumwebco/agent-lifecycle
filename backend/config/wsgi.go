package config

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strings"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/wsgi"
)

func WSGIApplication() http.Handler {
	if os.Getenv("DJANGO_SETTINGS_MODULE") == "" {
		os.Setenv("DJANGO_SETTINGS_MODULE", "agent_api.settings")
	}

	return wsgi.NewHandler()
}

func RunWSGIServer(addr string) error {
	handler := WSGIApplication()
	fmt.Printf("Starting WSGI server at %s\n", addr)
	return http.ListenAndServe(addr, handler)
}

func GetPythonWSGIApplication() string {
	cmd := exec.Command("python", "-c", `
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agent_api.settings')
from django.core.wsgi import get_wsgi_application
print(get_wsgi_application())
`)

	output, err := cmd.CombinedOutput()
	if err != nil {
		return ""
	}

	return strings.TrimSpace(string(output))
}
