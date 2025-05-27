package commands

import (
	"fmt"
	"os"
	"log"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/management"
)

var logger = log.New(os.Stdout, "[RunserverDaphne] ", log.LstdFlags)

type RunserverDaphneCommand struct {
	management.BaseCommand
}

func NewRunserverDaphneCommand() *RunserverDaphneCommand {
	cmd := &RunserverDaphneCommand{
		BaseCommand: management.NewBaseCommand("runserver_daphne", "Run the server with Daphne (HTTP + WebSocket)"),
	}
	return cmd
}

func (c *RunserverDaphneCommand) AddArguments(parser *management.ArgumentParser) {
	parser.AddArgument("--host", management.ArgumentConfig{
		Default: "0.0.0.0",
		Help:    "Host to bind to",
	})
	parser.AddArgument("--port", management.ArgumentConfig{
		Default: "8000",
		Help:    "Port to bind to",
	})
}

func (c *RunserverDaphneCommand) Handle(args map[string]interface{}) error {
	host := args["host"].(string)
	port := args["port"].(string)

	fmt.Printf("Starting Daphne server on %s:%s...\n", host, port)

	return core.CallPythonFunction("daphne.cli", "CommandLineInterface().run", []interface{}{
		[]string{
			"daphne",
			"-b", host,
			"-p", port,
			"agent_api.asgi:application",
		},
	})
}

func init() {
	management.RegisterCommand("runserver_daphne", NewRunserverDaphneCommand())
}
