package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/management"
)

func main() {
	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "Usage: %s [command] [options]\n\n", os.Args[0])
		fmt.Fprintf(os.Stderr, "Available commands:\n")
		for _, cmd := range management.GetAvailableCommands() {
			fmt.Fprintf(os.Stderr, "  %s\n", cmd)
		}
		fmt.Fprintf(os.Stderr, "\nUse '%s help [command]' for more information about a command.\n", os.Args[0])
	}

	flag.Parse()
	args := flag.Args()

	if len(args) == 0 {
		flag.Usage()
		os.Exit(1)
	}

	command := args[0]
	commandArgs := args[1:]

	setupDjangoGoEnvironment()

	err := management.ExecuteCommand(command, commandArgs)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func setupDjangoGoEnvironment() {
	dir, err := filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	if os.Getenv("DJANGO_SETTINGS_MODULE") == "" {
		settingsModule := "config.settings"
		os.Setenv("DJANGO_SETTINGS_MODULE", settingsModule)
	}

	pythonPath := os.Getenv("PYTHONPATH")
	parentDir := filepath.Dir(dir)
	if !strings.Contains(pythonPath, parentDir) {
		if pythonPath == "" {
			os.Setenv("PYTHONPATH", parentDir)
		} else {
			os.Setenv("PYTHONPATH", pythonPath+string(os.PathListSeparator)+parentDir)
		}
	}

	core.Initialize()
}
