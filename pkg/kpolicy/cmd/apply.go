package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

func NewApplyCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "apply",
		Short: "Apply Kubernetes policies",
		Long: `
Applies Kubernetes policies to resources or configurations.
`,
		RunE: func(cobraCmd *cobra.Command, args []string) error {
			log.GetInstance().Infof("Applying Kubernetes policies...")
			return nil
		},
	}

	return cmd
}
