package kcluster

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/spf13/cobra"
)

func NewKClusterCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	kclusterCmd := &cobra.Command{
		Use:   "kcluster",
		Short: "Manage Kubernetes virtual clusters",
		Long: `
The kcluster commands can be used to create and manage virtual Kubernetes clusters.
These are fully functional clusters running inside a namespace of another Kubernetes cluster.
`,
	}

	kclusterCmd.AddCommand(NewCreateCmd(globalFlags))
	kclusterCmd.AddCommand(NewListCmd(globalFlags))
	kclusterCmd.AddCommand(NewDeleteCmd(globalFlags))

	return kclusterCmd
}
