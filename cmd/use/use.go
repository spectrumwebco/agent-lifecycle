package use

import (
	"github.com/spectrumwebco/kled-beta/cmd/flags"
	"github.com/spectrumwebco/kled-beta/cmd/ide"
	"github.com/spectrumwebco/kled-beta/cmd/provider"
	"github.com/spf13/cobra"
)

// NewUseCmd returns a new root command
func NewUseCmd(flags *flags.GlobalFlags) *cobra.Command {
	useCmd := &cobra.Command{
		Use:   "use",
		Short: "Use DevPod resources",
	}

	// use provider
	useProviderCmd := provider.NewUseCmd(flags)
	useProviderCmd.Use = "provider"
	useCmd.AddCommand(useProviderCmd)

	// use ide
	useIDECmd := ide.NewUseCmd(flags)
	useIDECmd.Use = "ide"
	useCmd.AddCommand(useIDECmd)
	return useCmd
}
