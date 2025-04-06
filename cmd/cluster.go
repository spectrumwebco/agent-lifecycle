package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/devpod/cmd/kcluster"
	"github.com/spf13/cobra"
)

func NewClusterCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	clusterCmd := &cobra.Command{
		Use:     "cluster",
		Aliases: []string{"c", "k"},
		Short:   "Manage Kubernetes clusters",
		Long: `Commands for creating and managing Kubernetes clusters.

These are fully functional clusters running inside a namespace of another Kubernetes cluster.`,
	}

	clusterCmd.AddCommand(kcluster.NewCreateCmd(globalFlags))
	clusterCmd.AddCommand(kcluster.NewListCmd(globalFlags))
	clusterCmd.AddCommand(kcluster.NewDeleteCmd(globalFlags))
	
	clusterCmd.AddCommand(kcluster.NewKClusterCmd(globalFlags))
	
	return clusterCmd
}
