package commands

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"syscall"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/management"
)

type RunGRPCServerCommand struct {
	management.BaseCommand
	proc *exec.Cmd
}

func NewRunGRPCServerCommand() *RunGRPCServerCommand {
	cmd := &RunGRPCServerCommand{
		BaseCommand: management.NewBaseCommand("run_grpc_server", "Run the Go gRPC server for agent_runtime"),
		proc:        nil,
	}
	return cmd
}

func (c *RunGRPCServerCommand) Handle(args map[string]interface{}) error {
	fmt.Println("Starting Go gRPC server...")

	agentRuntimePath := core.GetSetting("AGENT_RUNTIME_PATH")
	if agentRuntimePath == "" {
		baseDir := core.GetSetting("BASE_DIR")
		agentRuntimePath = filepath.Join(baseDir, "..", "bin", "agent_runtime")
	}

	host := core.GetSetting("GRPC_SERVER_HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	port := core.GetSetting("GRPC_SERVER_PORT")
	if port == "" {
		port = "50051"
	}

	cmd := []string{
		agentRuntimePath,
		"serve",
		"--grpc-only",
		fmt.Sprintf("--grpc-host=%s", host),
		fmt.Sprintf("--grpc-port=%s", port),
	}

	fmt.Printf("Running command: %s\n", cmd)

	c.proc = exec.Command(cmd[0], cmd[1:]...)
	c.proc.Stdout = os.Stdout
	c.proc.Stderr = os.Stderr

	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		sig := <-sigChan
		fmt.Printf("Received signal %v, shutting down Go gRPC server...\n", sig)
		c.handleShutdown()
		os.Exit(0)
	}()

	err := c.proc.Start()
	if err != nil {
		if os.IsNotExist(err) {
			fmt.Printf("Agent runtime binary not found at %s\n", agentRuntimePath)
			fmt.Println("Falling back to Python gRPC server...")

			return core.CallPythonFunction("django_backend.grpc_server", "run_grpc_server", []interface{}{})
		}
		return fmt.Errorf("Error starting Go gRPC server: %v", err)
	}

	fmt.Printf("Go gRPC server started on %s:%s\n", host, port)

	err = c.proc.Wait()
	if err != nil {
		if c.proc.ProcessState != nil {
			exitCode := c.proc.ProcessState.ExitCode()
			if exitCode != 0 {
				return fmt.Errorf("Go gRPC server exited with code %d", exitCode)
			}
		}
		return fmt.Errorf("Error waiting for Go gRPC server: %v", err)
	}

	fmt.Println("Go gRPC server stopped")
	return nil
}

func (c *RunGRPCServerCommand) handleShutdown() {
	if c.proc != nil && c.proc.Process != nil {
		fmt.Println("Shutting down Go gRPC server...")
		
		err := c.proc.Process.Signal(syscall.SIGTERM)
		if err != nil {
			fmt.Printf("Error sending SIGTERM to process: %v\n", err)
			c.proc.Process.Kill()
		}
		
		c.proc.Wait()
		fmt.Println("Go gRPC server stopped")
	}
}

func init() {
	management.RegisterCommand("run_grpc_server", NewRunGRPCServerCommand())
}
