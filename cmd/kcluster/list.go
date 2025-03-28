package kcluster

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

func NewListCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	listCmd := &cobra.Command{
		Use:   "list",
		Short: "List virtual clusters",
		Long: `
Lists all virtual Kubernetes clusters in the specified namespace.
`,
		RunE: func(cmd *cobra.Command, args []string) error {
			log.GetInstance().Info("Listing kclusters...")
			return nil
		},
	}

	return listCmd
}
