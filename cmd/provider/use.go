package provider

import (
	"context"
	"fmt"
	"io"

	"github.com/loft-sh/devpod/cmd/completion"
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/devpod/pkg/client/clientimplementation"
	"github.com/loft-sh/devpod/pkg/config"
	options2 "github.com/loft-sh/devpod/pkg/options"
	provider2 "github.com/loft-sh/devpod/pkg/provider"
	"github.com/loft-sh/devpod/pkg/workspace"
	"github.com/loft-sh/log"
	"github.com/pkg/errors"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
)

// UseCmd holds the use cmd flags
type UseCmd struct {
	flags.GlobalFlags

	Reconfigure   bool
	SingleMachine bool
	Options       []string

	// only for testing
	SkipInit bool
}

// NewUseCmd creates a new command
func NewUseCmd(flags *flags.GlobalFlags) *cobra.Command {
	cmd := &UseCmd{
		GlobalFlags: *flags,
	}
	useCmd := &cobra.Command{
		Use:   "use [name]",
		Short: "Configure an existing provider and set as default",
		RunE: func(_ *cobra.Command, args []string) error {
			if len(args) != 1 {
				return fmt.Errorf("please specify the provider to use")
			}

			return cmd.Run(context.Background(), args[0])
		},
		ValidArgsFunction: func(rootCmd *cobra.Command, args []string, toComplete string) ([]string, cobra.ShellCompDirective) {
			return completion.GetProviderSuggestions(rootCmd, cmd.Context, cmd.Provider, args, toComplete, cmd.Owner, log.Default)
		},
	}

	AddFlags(useCmd, cmd)
	return useCmd
}

func AddFlags(useCmd *cobra.Command, cmd *UseCmd) {
	useCmd.Flags().BoolVar(&cmd.SingleMachine, "single-machine", false, "If enabled will use a single machine for all workspaces")
	useCmd.Flags().BoolVar(&cmd.Reconfigure, "reconfigure", false, "If enabled will not merge existing provider config")
	useCmd.Flags().StringArrayVarP(&cmd.Options, "option", "o", []string{}, "Provider option in the form KEY=VALUE")

	useCmd.Flags().BoolVar(&cmd.SkipInit, "skip-init", false, "ONLY FOR TESTING: If true will skip init")
	_ = useCmd.Flags().MarkHidden("skip-init")
}

// Run runs the command logic
func (cmd *UseCmd) Run(ctx context.Context, providerName string) error {
	kledConfig, err := config.LoadConfig(cmd.Context, cmd.Provider) // TODO: Update variable name to reflect Kled branding
	if err != nil {
		return err
	}

	providerWithOptions, err := workspace.FindProvider(kledConfig, providerName, log.Default)
	if err != nil {
		return err
	}

	// should reconfigure?
	shouldReconfigure := cmd.Reconfigure || len(cmd.Options) > 0 || providerWithOptions.State == nil || cmd.SingleMachine
	if shouldReconfigure {
		return ConfigureProvider(ctx, providerWithOptions.Config, kledConfig.DefaultContext, cmd.Options, cmd.Reconfigure, cmd.SkipInit, false, &cmd.SingleMachine, log.Default)
	} else {
		log.Default.Infof("To reconfigure provider %s, run with '--reconfigure' to reconfigure the provider", providerWithOptions.Config.Name)
	}

	// set options
	defaultContext := kledConfig.Current()
	defaultContext.DefaultProvider = providerWithOptions.Config.Name

	// save provider config
	err = config.SaveConfig(kledConfig)
	if err != nil {
		return errors.Wrap(err, "save config")
	}

	// print success message
	log.Default.Donef("Successfully switched default provider to '%s'", providerWithOptions.Config.Name)
	return nil
}

func ConfigureProvider(ctx context.Context, provider *provider2.ProviderConfig, context string, userOptions []string, reconfigure, skipInit, skipSubOptions bool, singleMachine *bool, log log.Logger) error {
	// set options
	kledConfig, err := setOptions(ctx, provider, context, userOptions, reconfigure, false, skipInit, skipSubOptions, singleMachine, log)
	if err != nil {
		return err
	}

	// set options
	defaultContext := kledConfig.Current()
	defaultContext.DefaultProvider = provider.Name

	// save provider config
	err = config.SaveConfig(kledConfig)
	if err != nil {
		return errors.Wrap(err, "save config")
	}

	log.Donef("Successfully configured provider '%s'", provider.Name)
	return nil
}

func setOptions(
	ctx context.Context,
	provider *provider2.ProviderConfig,
	context string,
	userOptions []string,
	reconfigure,
	skipRequired,
	skipInit,
	skipSubOptions bool,
	singleMachine *bool,
	log log.Logger,
) (*config.Config, error) {
	kledConfig, err := config.LoadConfig(context, "") // TODO: Update variable name to reflect Kled branding
	if err != nil {
		return nil, err
	}

	// parse options
	options, err := provider2.ParseOptions(userOptions)
	if err != nil {
		return nil, errors.Wrap(err, "parse options")
	}

	// merge with old values
	if !reconfigure {
		for k, v := range kledConfig.ProviderOptions(provider.Name) {
			_, ok := options[k]
			if !ok && v.UserProvided {
				options[k] = v.Value
			}
		}
	}

	// fill defaults
	kledConfig, err = options2.ResolveOptions(ctx, kledConfig, provider, options, skipRequired, skipSubOptions, singleMachine, log)
	if err != nil {
		return nil, errors.Wrap(err, "resolve options")
	}

	// run init command
	if !skipInit {
		stdout := log.Writer(logrus.InfoLevel, false)
		defer stdout.Close()

		stderr := log.Writer(logrus.ErrorLevel, false)
		defer stderr.Close()

		err = initProvider(ctx, devPodConfig, provider, stdout, stderr)
		if err != nil {
			return nil, err
		}
	}

	return kledConfig, nil
}

func initProvider(ctx context.Context, kledConfig *config.Config, provider *provider2.ProviderConfig, stdout, stderr io.Writer) error {
	// run init command
	err := clientimplementation.RunCommandWithBinaries(
		ctx,
		"init",
		provider.Exec.Init,
		kledConfig.DefaultContext,
		nil,
		nil,
		kledConfig.ProviderOptions(provider.Name),
		provider,
		nil,
		nil,
		stdout,
		stderr,
		log.Default,
	)
	if err != nil {
		return errors.Wrap(err, "init")
	}
	if kledConfig.Current().Providers == nil {
		kledConfig.Current().Providers = map[string]*config.ProviderConfig{}
	}
	if kledConfig.Current().Providers[provider.Name] == nil {
		kledConfig.Current().Providers[provider.Name] = &config.ProviderConfig{}
	}
	kledConfig.Current().Providers[provider.Name].Initialized = true
	return nil
}
