package utils

import (
	"context"
	"fmt"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"google.golang.org/grpc"
	"google.golang.org/grpc/reflection"
)

type AgentRuntimeGrpcServer struct {
	host      string
	port      int
	server    *grpc.Server
	isRunning bool
}

func NewAgentRuntimeGrpcServer(host string, port int, maxWorkers int) *AgentRuntimeGrpcServer {
	if host == "" {
		host = "0.0.0.0"
	}
	if port == 0 {
		port = 50051
	}
	if maxWorkers == 0 {
		maxWorkers = 10
	}

	server := grpc.NewServer()
	reflection.Register(server)

	return &AgentRuntimeGrpcServer{
		host:      host,
		port:      port,
		server:    server,
		isRunning: false,
	}
}

func (s *AgentRuntimeGrpcServer) Start() *AgentRuntimeGrpcServer {
	serverAddress := fmt.Sprintf("%s:%d", s.host, s.port)
	listener, err := net.Listen("tcp", serverAddress)
	if err != nil {
		log.Fatalf("Failed to listen on %s: %v", serverAddress, err)
	}

	go func() {
		log.Printf("gRPC server started on %s", serverAddress)
		s.isRunning = true
		if err := s.server.Serve(listener); err != nil {
			log.Fatalf("Failed to serve: %v", err)
		}
	}()

	return s
}

func (s *AgentRuntimeGrpcServer) Stop(grace time.Duration) {
	if s.isRunning {
		if grace > 0 {
			ctx, cancel := context.WithTimeout(context.Background(), grace)
			defer cancel()
			s.server.GracefulStop()
			<-ctx.Done()
		} else {
			s.server.Stop()
		}
		s.isRunning = false
		log.Println("gRPC server stopped")
	}
}

func (s *AgentRuntimeGrpcServer) WaitForTermination() {
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

	sig := <-sigCh
	log.Printf("Received signal %v, shutting down gRPC server...", sig)
	s.Stop(5 * time.Second)
}

func (s *AgentRuntimeGrpcServer) RegisterService(registerFunc func(*grpc.Server)) {
	registerFunc(s.server)
}

func RunGrpcServer() {
	settings := core.GetDjangoSettings()
	host := settings.GetString("GRPC_SERVER_HOST", "0.0.0.0")
	port := settings.GetInt("GRPC_SERVER_PORT", 50051)

	server := NewAgentRuntimeGrpcServer(host, port, 10)
	server.Start()

	registerPythonServices(server)

	server.WaitForTermination()
}

func registerPythonServices(server *AgentRuntimeGrpcServer) {
	script := `
import os
import sys
import importlib
import logging
from django.conf import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("grpc-server")

def register_python_services():
    """Register Python-based gRPC services."""
    try:
        # Import and register services from Django apps
        for app in settings.INSTALLED_APPS:
            try:
                module = importlib.import_module(f"{app}.grpc_services")
                if hasattr(module, "register_services"):
                    logger.info(f"Registering gRPC services from {app}")
                    module.register_services()
            except ImportError:
                # App doesn't have grpc_services module
                pass
            except Exception as e:
                logger.error(f"Error registering gRPC services from {app}: {e}")
        
        return True
    except Exception as e:
        logger.error(f"Error registering Python gRPC services: {e}")
        return False

# Register Python services
success = register_python_services()
print("SUCCESS" if success else "FAILURE")
`

	cmd := core.ExecutePythonScript(script)
	output, err := cmd.CombinedOutput()
	if err != nil {
		log.Printf("Error registering Python services: %v", err)
		log.Printf("Output: %s", string(output))
		return
	}

	log.Printf("Python services registration: %s", string(output))
}

func main() {
	RunGrpcServer()
}
