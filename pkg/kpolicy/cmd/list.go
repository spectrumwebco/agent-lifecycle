package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

func NewListCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List Kubernetes policies",
		Long: `
Lists all Kubernetes policies in the current context.
`,
		RunE: func(cobraCmd *cobra.Command, args []string) error {
			log.GetInstance().Infof("Listing Kubernetes policies...")
			return nil
		},
	}

	return cmd
}
