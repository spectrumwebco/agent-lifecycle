package cmd

import (
	"fmt"
	"os"
	"os/exec"

	"github.com/loft-sh/devpod/cmd/agent" // TODO: Update import paths when repository is renamed
	"github.com/loft-sh/devpod/cmd/completion"
	"github.com/loft-sh/devpod/cmd/context"
	"github.com/loft-sh/devpod/cmd/flags"
	"github.com/loft-sh/devpod/cmd/helper"
	"github.com/loft-sh/devpod/cmd/ide"
	"github.com/loft-sh/devpod/cmd/kcluster"
	"github.com/loft-sh/devpod/cmd/machine"
	"github.com/loft-sh/devpod/cmd/pro"
	"github.com/loft-sh/devpod/cmd/provider"
	"github.com/loft-sh/devpod/cmd/use"
	"github.com/loft-sh/devpod/pkg/client/clientimplementation"
	"github.com/loft-sh/devpod/pkg/config"
	"github.com/loft-sh/devpod/pkg/telemetry"
	log2 "github.com/loft-sh/log"
	"github.com/loft-sh/log/terminal"
	"github.com/sirupsen/logrus"
	"github.com/spf13/cobra"
	"golang.org/x/crypto/ssh"
)

var globalFlags *flags.GlobalFlags

// NewRootCmd returns a new root command
func NewRootCmd() *cobra.Command {
	return &cobra.Command{
		Use:           "kled",
		Short:         "Kled - Workspace and Kubernetes Development Environment",
		Long: `Kled is a unified tool for managing development environments.

It provides commands for:
- Workspace management (formerly kled)
- Kubernetes cluster management (formerly kcluster)
- Application space management (formerly kledspace)
- Policy management (formerly kpolicy)`,
		SilenceUsage:  true,
		SilenceErrors: true,
		PersistentPreRunE: func(cobraCmd *cobra.Command, args []string) error {
			if globalFlags.LogOutput == "json" {
				log2.Default.SetFormat(log2.JSONFormat)
			} else if globalFlags.LogOutput == "raw" {
				log2.Default.SetFormat(log2.RawFormat)
			} else if globalFlags.LogOutput != "plain" {
				return fmt.Errorf("unrecognized log format %s, needs to be either plain or json", globalFlags.LogOutput)
			}

			if globalFlags.Silent {
				log2.Default.SetLevel(logrus.FatalLevel)
			} else if globalFlags.Debug {
				log2.Default.SetLevel(logrus.DebugLevel)
			} else if os.Getenv(clientimplementation.KledDebug) == "true" {
				log2.Default.SetLevel(logrus.DebugLevel)
			}

			if globalFlags.KledHome != "" {
				_ = os.Setenv(config.KLED_HOME, globalFlags.KledHome)
			}

			kledConfig, err := config.LoadConfig(globalFlags.Context, globalFlags.Provider)
			if err == nil {
				telemetry.StartCLI(kledConfig, cobraCmd)
			}

			return nil
		},
		PersistentPostRunE: func(cmd *cobra.Command, args []string) error {
			if globalFlags.KledHome != "" {
				_ = os.Unsetenv(config.KLED_HOME)
			}

			return nil
		},
	}
}

// Execute adds all child commands to the root command and sets flags appropriately.
// This is called by main.main(). It only needs to happen once to the rootCmd.
func Execute() {
	// build the root command
	rootCmd := BuildRoot()

	// execute command
	err := rootCmd.Execute()
	telemetry.CollectorCLI.RecordCLI(err)
	telemetry.CollectorCLI.Flush()
	if err != nil {
		//nolint:all
		if sshExitErr, ok := err.(*ssh.ExitError); ok {
			os.Exit(sshExitErr.ExitStatus())
		}

		//nolint:all
		if execExitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(execExitErr.ExitCode())
		}

		if globalFlags.Debug {
			log2.Default.Fatalf("%+v", err)
		} else {
			if rootCmd.Annotations == nil || rootCmd.Annotations[agent.AgentExecutedAnnotation] != "true" {
				if terminal.IsTerminalIn {
					log2.Default.Error("Try using the --debug flag to see a more verbose output")
				} else if os.Getenv(telemetry.UIEnvVar) == "true" {
					log2.Default.Error("Try enabling Debug mode under Settings to see a more verbose output")
				}
			}
			log2.Default.Fatal(err)
		}
	}
}

// BuildRoot creates a new root command from the
func BuildRoot() *cobra.Command {
	rootCmd := NewRootCmd()
	persistentFlags := rootCmd.PersistentFlags()
	globalFlags = flags.SetGlobalFlags(persistentFlags)
	_ = completion.RegisterFlagCompletionFuns(rootCmd, globalFlags)

	rootCmd.AddCommand(agent.NewAgentCmd(globalFlags))
	rootCmd.AddCommand(provider.NewProviderCmd(globalFlags))
	rootCmd.AddCommand(use.NewUseCmd(globalFlags))
	rootCmd.AddCommand(helper.NewHelperCmd(globalFlags))
	rootCmd.AddCommand(ide.NewIDECmd(globalFlags))
	rootCmd.AddCommand(machine.NewMachineCmd(globalFlags))
	rootCmd.AddCommand(context.NewContextCmd(globalFlags))
	rootCmd.AddCommand(pro.NewProCmd(globalFlags, log2.Default))
	rootCmd.AddCommand(NewVersionCmd())
	rootCmd.AddCommand(NewUpgradeCmd())
	rootCmd.AddCommand(NewPingCmd(globalFlags))
	
	rootCmd.AddCommand(NewWorkspaceCmd(globalFlags))
	rootCmd.AddCommand(NewClusterCmd(globalFlags))
	rootCmd.AddCommand(NewSpaceCmd(globalFlags))
	rootCmd.AddCommand(NewPolicyCmd(globalFlags))
	
	rootCmd.AddCommand(kcluster.NewKClusterCmd(globalFlags))
	rootCmd.AddCommand(NewUpCmd(globalFlags))
	rootCmd.AddCommand(NewDeleteCmd(globalFlags))
	rootCmd.AddCommand(NewSSHCmd(globalFlags))
	rootCmd.AddCommand(NewStopCmd(globalFlags))
	rootCmd.AddCommand(NewListCmd(globalFlags))
	rootCmd.AddCommand(NewStatusCmd(globalFlags))
	rootCmd.AddCommand(NewBuildCmd(globalFlags))
	rootCmd.AddCommand(NewLogsDaemonCmd(globalFlags))
	rootCmd.AddCommand(NewExportCmd(globalFlags))
	rootCmd.AddCommand(NewImportCmd(globalFlags))
	rootCmd.AddCommand(NewLogsCmd(globalFlags))
	rootCmd.AddCommand(NewTroubleshootCmd(globalFlags))
	
	return rootCmd
}
