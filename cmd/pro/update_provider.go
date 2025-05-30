package pro

import (
	"context"
	"fmt"
	"strings"

	"github.com/loft-sh/devpod/cmd/pro/flags"
	providercmd "github.com/loft-sh/devpod/cmd/provider"
	"github.com/loft-sh/devpod/pkg/config"
	"github.com/loft-sh/devpod/pkg/workspace"
	"github.com/loft-sh/log"
	"github.com/spf13/cobra"
)

// UpdateProviderCmd holds the cmd flags
type UpdateProviderCmd struct {
	*flags.GlobalFlags
	Log log.Logger

	Host     string
	Instance string
}

// NewUpdateProviderCmd creates a new command
func NewUpdateProviderCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	cmd := &UpdateProviderCmd{
		GlobalFlags: globalFlags,
		Log:         log.GetInstance(),
	}
	c := &cobra.Command{
		Use:    "update-provider [new-version]",
		Short:  "Update platform provider",
		Hidden: true,
		RunE: func(cobraCmd *cobra.Command, args []string) error {
			return cmd.Run(cobraCmd.Context(), args)
		},
	}

	c.Flags().StringVar(&cmd.Host, "host", "", "The pro instance to use")
	_ = c.MarkFlagRequired("host")

	return c
}

func (cmd *UpdateProviderCmd) Run(ctx context.Context, args []string) error {
	if len(args) != 1 {
		return fmt.Errorf("new version is missing")
	}
	newVersion := args[0]

	kledConfig, err := config.LoadConfig(cmd.Context, cmd.Provider) // TODO: Update variable name to reflect Kled branding
	if err != nil {
		return err
	}

	provider, err := workspace.ProviderFromHost(ctx, kledConfig, cmd.Host, cmd.Log)
	if err != nil {
		return fmt.Errorf("load provider: %w", err)
	}
	if provider.Source.Internal {
		return nil
	}
	providerSource, err := workspace.ResolveProviderSource(kledConfig, provider.Name, cmd.Log)
	if err != nil {
		return fmt.Errorf("resolve provider source %s: %w", provider.Name, err)
	}
	splitted := strings.Split(providerSource, "@")
	if len(splitted) == 0 {
		return fmt.Errorf("no provider source found %s", providerSource)
	}
	providerSource = splitted[0] + "@" + newVersion

	_, err = workspace.UpdateProvider(kledConfig, provider.Name, providerSource, cmd.Log)
	if err != nil {
		return fmt.Errorf("update provider %s: %w", provider.Name, err)
	}

	err = providercmd.ConfigureProvider(ctx, provider, kledConfig.DefaultContext, []string{}, true, true, true, nil, log.Discard)
	if err != nil {
		return fmt.Errorf("configure provider, please retry with 'kled provider use %s --reconfigure': %w", provider.Name, err)
	}

	return nil
}
