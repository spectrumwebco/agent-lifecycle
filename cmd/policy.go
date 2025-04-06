package cmd

import (
	"github.com/loft-sh/devpod/cmd/flags"
	policycmd "github.com/loft-sh/devpod/pkg/kpolicy/cmd"
	"github.com/spf13/cobra"
)

func NewPolicyCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	policyCmd := &cobra.Command{
		Use:     "policy",
		Aliases: []string{"p"},
		Short:   "Manage Kubernetes policies",
		Long:    `Commands for validating and managing Kubernetes policies`,
	}
	
	policyCmd.AddCommand(policycmd.NewValidateCmd(globalFlags))
	policyCmd.AddCommand(policycmd.NewApplyCmd(globalFlags))
	policyCmd.AddCommand(policycmd.NewListCmd(globalFlags))
	
	policyCmd.AddCommand(policycmd.NewKPolicyCmd(globalFlags))
	
	return policyCmd
}
