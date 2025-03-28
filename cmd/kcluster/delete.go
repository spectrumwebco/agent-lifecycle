package kcluster

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

func NewDeleteCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	deleteCmd := &cobra.Command{
		Use:   "delete",
		Short: "Delete a virtual cluster",
		Long: `
Deletes a virtual Kubernetes cluster from the specified namespace.
`,
		RunE: func(cmd *cobra.Command, args []string) error {
			log.GetInstance().Info("Deleting kcluster...")
			return nil
		},
	}

	return deleteCmd
}
