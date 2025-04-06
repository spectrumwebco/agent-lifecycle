package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

func NewValidateCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "validate",
		Short: "Validate Kubernetes policies",
		Long: `
Validates Kubernetes policies against resources or configurations.
`,
		RunE: func(cobraCmd *cobra.Command, args []string) error {
			log.GetInstance().Infof("Validating Kubernetes policies...")
			return nil
		},
	}

	return cmd
}
