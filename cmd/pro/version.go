package pro

import (
	"bytes"
	"context"
	"fmt"

	"github.com/loft-sh/devpod/cmd/pro/flags"
	"github.com/spectrumwebco/kled-pro/pkg/client/clientimplementation"
	"github.com/loft-sh/devpod/pkg/config"
	"github.com/spectrumwebco/kled-pro/pkg/provider"
	"github.com/loft-sh/log"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

// VersionCmd holds the cmd flags
type VersionCmd struct {
	*flags.GlobalFlags
	Log log.Logger

	Host string
}

// NewVersionCmd creates a new command
func NewVersionCmd(globalFlags *flags.GlobalFlags) *cobra.Command {
	cmd := &VersionCmd{
		GlobalFlags: globalFlags,
		Log:         log.GetInstance(),
	}
	c := &cobra.Command{
		Use:    "version",
		Short:  "Get version",
		Hidden: true,
		RunE: func(cobraCmd *cobra.Command, args []string) error {
			kledConfig, provider, err := findProProvider(cobraCmd.Context(), cmd.Context, cmd.Provider, cmd.Host, cmd.Log) // TODO: Update variable name to reflect Kled branding
			if err != nil {
				return err
			}

			return cmd.Run(cobraCmd.Context(), kledConfig, provider)
		},
	}

	c.Flags().StringVar(&cmd.Host, "host", "", "The pro instance to use")
	_ = c.MarkFlagRequired("host")

	return c
}

func (cmd *VersionCmd) Run(ctx context.Context, kledConfig *config.Config, providerConfig *provider.ProviderConfig) error {
	opts := kledConfig.ProviderOptions(providerConfig.Name)
	opts[provider.PROVIDER_ID] = config.OptionValue{Value: providerConfig.Name}
	opts[provider.PROVIDER_CONTEXT] = config.OptionValue{Value: cmd.Context}

	var buf bytes.Buffer
	// ignore --debug because we tunnel json through stdio
	cmd.Log.SetLevel(logrus.InfoLevel)

	err := clientimplementation.RunCommandWithBinaries(
		ctx,
		"getVersion",
		providerConfig.Exec.Proxy.Get.Version,
		kledConfig.DefaultContext,
		nil,
		nil,
		opts,
		providerConfig,
		nil,
		nil,
		&buf,
		nil,
		cmd.Log)
	if err != nil {
		return fmt.Errorf("get version: %w", err)
	}

	fmt.Print(buf.String())

	return nil
}
