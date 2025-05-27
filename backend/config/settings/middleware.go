package settings

import (
	"github.com/gin-gonic/gin"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/middleware"
)


func SetupMiddleware(router *gin.Engine) {
	router.Use(middleware.SecurityMiddleware())
	
	router.Use(middleware.SessionMiddleware())
	
	router.Use(middleware.CommonMiddleware())
	
	router.Use(middleware.CsrfMiddleware())
	
	router.Use(middleware.AuthenticationMiddleware())
	
	router.Use(middleware.MessagesMiddleware())
	
	router.Use(middleware.XFrameOptionsMiddleware())
	
	router.Use(middleware.CustomSecurityMiddleware())
	
	router.Use(middleware.RequestLoggingMiddleware())
	
	router.Use(middleware.PerformanceMiddleware())
	
	router.Use(middleware.AgentIntegrationMiddleware())
}

func GetMiddlewareList() []gin.HandlerFunc {
	return []gin.HandlerFunc{
		middleware.SecurityMiddleware(),
		middleware.SessionMiddleware(),
		middleware.CommonMiddleware(),
		middleware.CsrfMiddleware(),
		middleware.AuthenticationMiddleware(),
		middleware.MessagesMiddleware(),
		middleware.XFrameOptionsMiddleware(),
		middleware.CustomSecurityMiddleware(),
		middleware.RequestLoggingMiddleware(),
		middleware.PerformanceMiddleware(),
		middleware.AgentIntegrationMiddleware(),
	}
}

func GetDjangoMiddlewareList() []string {
	return []string{
		"django.middleware.security.SecurityMiddleware",
		"django.contrib.sessions.middleware.SessionMiddleware",
		"django.middleware.common.CommonMiddleware",
		"django.middleware.csrf.CsrfViewMiddleware",
		"django.contrib.auth.middleware.AuthenticationMiddleware",
		"django.contrib.messages.middleware.MessageMiddleware",
		"django.middleware.clickjacking.XFrameOptionsMiddleware",
		"apps.app.middleware.security.SecurityMiddleware",
		"apps.app.middleware.request_logging.RequestLoggingMiddleware",
		"apps.app.middleware.performance.PerformanceMiddleware",
		"apps.app.middleware.agent_integration.AgentIntegrationMiddleware",
	}
}
