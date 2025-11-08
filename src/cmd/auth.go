package cmd

import (
    "github.com/spf13/cobra"

    "evalarena-cli/internal/auth"
)

func init() {
    authCmd := &cobra.Command{Use: "auth", Short: "Authentication commands"}

    loginCmd := &cobra.Command{
        Use:   "login",
        Short: "Login with API token",
        RunE: func(cmd *cobra.Command, args []string) error {
            return auth.Login()
        },
    }
    logoutCmd := &cobra.Command{
        Use:   "logout",
        Short: "Logout and remove stored credentials",
        RunE: func(cmd *cobra.Command, args []string) error {
            return auth.Logout()
        },
    }

    authCmd.AddCommand(loginCmd, logoutCmd)
    RegisterCommand(authCmd)
}



