package main

import (
	"os"

	"github.com/loft-sh/devpod/cmd"
	"github.com/loft-sh/devpod/pkg/log"
)

func main() {
	rootCmd := cmd.NewRootCmd()
	if err := rootCmd.Execute(); err != nil {
		log.GetInstance().Fatalf(err.Error())
		os.Exit(1)
	}
}
