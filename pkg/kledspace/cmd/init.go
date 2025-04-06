package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

func NewInitCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "init",
		Short: "Initialize a new application space",
		Long: `
Initializes a new application space in the current directory.
This creates a kledspace.yaml file with default configuration.
`,
		RunE: func(cobraCmd *cobra.Command, args []string) error {
			log.GetInstance().Infof("Initializing new application space...")
			return nil
		},
	}

	return cmd
}
