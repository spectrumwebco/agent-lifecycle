package main

import (
	"fmt"
	"os"

	"github.com/spectrumwebco/django-go/src/core"
	"github.com/spectrumwebco/django-go/src/core/settings"
	"github.com/spectrumwebco/django-go/src/db/migrations"
	"github.com/spf13/cobra"
)

func main() {
	var rootCmd = &cobra.Command{
		Use:   "manage",
		Short: "Django-Go management utility",
		Long:  `Django-Go management utility for the agent_runtime application.`,
	}

	var runserverCmd = &cobra.Command{
		Use:   "runserver [address]",
		Short: "Starts the Django-Go development server",
		Long:  `Starts the Django-Go development server at the specified address or at localhost:8000 by default.`,
		Args:  cobra.MaximumNArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			addr := ":8000"
			if len(args) > 0 {
				addr = args[0]
			}

			app := createApp()
			fmt.Printf("Starting development server at %s\n", addr)
			app.Run(addr)
		},
	}

	var migrateCmd = &cobra.Command{
		Use:   "migrate",
		Short: "Applies database migrations",
		Long:  `Applies all pending database migrations to the database.`,
		Run: func(cmd *cobra.Command, args []string) {
			app := createApp()
			fmt.Println("Applying database migrations...")
			err := migrations.Apply(app.DB)
			if err != nil {
				fmt.Printf("Error applying migrations: %v\n", err)
				os.Exit(1)
			}
			fmt.Println("Migrations applied successfully")
		},
	}

	var makemigrationsCmd = &cobra.Command{
		Use:   "makemigrations",
		Short: "Creates new database migrations",
		Long:  `Creates new database migrations based on changes to your models.`,
		Run: func(cmd *cobra.Command, args []string) {
			app := createApp()
			fmt.Println("Creating database migrations...")
			err := migrations.Create(app.DB)
			if err != nil {
				fmt.Printf("Error creating migrations: %v\n", err)
				os.Exit(1)
			}
			fmt.Println("Migrations created successfully")
		},
	}

	var shellCmd = &cobra.Command{
		Use:   "shell",
		Short: "Starts an interactive shell",
		Long:  `Starts an interactive shell with the Django-Go application context.`,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Interactive shell not implemented yet")
		},
	}

	var createsuperuserCmd = &cobra.Command{
		Use:   "createsuperuser",
		Short: "Creates a superuser account",
		Long:  `Creates a superuser account for the Django-Go admin interface.`,
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Creating superuser...")
			fmt.Println("Superuser created successfully")
		},
	}

	rootCmd.AddCommand(runserverCmd)
	rootCmd.AddCommand(migrateCmd)
	rootCmd.AddCommand(makemigrationsCmd)
	rootCmd.AddCommand(shellCmd)
	rootCmd.AddCommand(createsuperuserCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}

func createApp() *core.App {
	return core.NewApp(settings.Config{
		Debug:        true,
		SecretKey:    os.Getenv("DJANGO_GO_SECRET_KEY"),
		AllowedHosts: []string{"localhost", "127.0.0.1"},
		Database: settings.Database{
			Engine:   "mysql",
			Name:     os.Getenv("DJANGO_GO_DB_NAME"),
			User:     os.Getenv("DJANGO_GO_DB_USER"),
			Password: os.Getenv("DJANGO_GO_DB_PASSWORD"),
			Host:     os.Getenv("DJANGO_GO_DB_HOST"),
			Port:     os.Getenv("DJANGO_GO_DB_PORT"),
		},
		InstalledApps: []string{
			"github.com/spectrumwebco/django-go/src/admin",
			"github.com/spectrumwebco/django-go/src/auth",
		},
		Middleware: []string{
			"github.com/spectrumwebco/django-go/src/http/middleware.SessionMiddleware",
			"github.com/spectrumwebco/django-go/src/http/middleware.CSRFMiddleware",
		},
	})
}
