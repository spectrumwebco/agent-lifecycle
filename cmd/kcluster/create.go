package kcluster

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

func NewCreateCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	createCmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new virtual cluster",
		Long: `
Creates a new virtual Kubernetes cluster in the specified namespace.
`,
		RunE: func(cmd *cobra.Command, args []string) error {
			log.GetInstance().Info("Creating kcluster...")
			return nil
		},
	}

	return createCmd
}
