package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/spf13/cobra"
)

func NewKPolicyCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	kpolicyCmd := &cobra.Command{
		Use:   "kpolicy",
		Short: "Manage Kubernetes policies",
		Long: `
The kpolicy commands can be used to validate and manage Kubernetes policies.
These policies help enforce security and compliance standards in your clusters.
`,
	}

	kpolicyCmd.AddCommand(NewValidateCmd(globalFlags))
	kpolicyCmd.AddCommand(NewApplyCmd(globalFlags))
	kpolicyCmd.AddCommand(NewListCmd(globalFlags))

	return kpolicyCmd
}
