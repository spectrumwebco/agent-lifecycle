package commands

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/management"
)

var logger = log.New(os.Stdout, "[StartGRPCServer] ", log.LstdFlags)

type StartGRPCServerCommand struct {
	management.BaseCommand
}

func NewStartGRPCServerCommand() *StartGRPCServerCommand {
	cmd := &StartGRPCServerCommand{
		BaseCommand: management.NewBaseCommand("start_grpc_server", "Start the Go gRPC server for agent_runtime"),
	}
	return cmd
}

func (c *StartGRPCServerCommand) AddArguments(parser *management.ArgumentParser) {
	parser.AddArgument("--port", management.ArgumentConfig{
		Type:    "int",
		Default: 50051,
		Help:    "Port for the gRPC server to listen on",
	})
	parser.AddArgument("--host", management.ArgumentConfig{
		Type:    "string",
		Default: "0.0.0.0",
		Help:    "Host for the gRPC server to bind to",
	})
}

func (c *StartGRPCServerCommand) Handle(args map[string]interface{}) error {
	port := args["port"].(int)
	host := args["host"].(string)

	fmt.Printf("Starting Go gRPC server on %s:%d...\n", host, port)

	baseDir := core.GetSetting("BASE_DIR")
	repoRoot := filepath.Dir(filepath.Dir(filepath.Dir(baseDir)))
	serverScriptPath := filepath.Join(repoRoot, "scripts", "simple_grpc_server.go")

	if _, err := os.Stat(serverScriptPath); os.IsNotExist(err) {
		return fmt.Errorf("Server script not found at %s", serverScriptPath)
	}

	scriptDir := filepath.Dir(serverScriptPath)
	if err := os.Chdir(scriptDir); err != nil {
		return fmt.Errorf("Failed to change directory to %s: %v", scriptDir, err)
	}

	fmt.Println("Building Go gRPC server...")
	buildCmd := exec.Command("go", "build", "-o", "simple_grpc_server", "simple_grpc_server.go")
	buildOutput, err := buildCmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("Failed to build Go gRPC server: %v\nOutput: %s", err, buildOutput)
	}

	fmt.Println("Starting Go gRPC server process...")
	serverCmd := exec.Command("./simple_grpc_server")
	serverCmd.Stdout = os.Stdout
	serverCmd.Stderr = os.Stderr

	if err := serverCmd.Start(); err != nil {
		return fmt.Errorf("Failed to start server process: %v", err)
	}

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	time.Sleep(1 * time.Second)

	if serverCmd.Process == nil {
		return fmt.Errorf("Server process failed to start")
	}

	fmt.Printf("Go gRPC server running on %s:%d\n", host, port)

	go func() {
		for {
			if serverCmd.ProcessState != nil && serverCmd.ProcessState.Exited() {
				fmt.Printf("Server process exited unexpectedly with code %d\n", serverCmd.ProcessState.ExitCode())
				break
			}
			time.Sleep(100 * time.Millisecond)
		}
	}()

	<-sigChan
	fmt.Println("Received shutdown signal, stopping server...")
	
	if err := serverCmd.Process.Signal(syscall.SIGTERM); err != nil {
		fmt.Printf("Error sending SIGTERM to server process: %v\n", err)
		serverCmd.Process.Kill()
	}

	serverCmd.Wait()
	return nil
}

func init() {
	management.RegisterCommand("start_grpc_server", NewStartGRPCServerCommand())
}
