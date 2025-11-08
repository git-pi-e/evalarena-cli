package cmd

import (
    "context"
    "fmt"
    "time"

    "github.com/spf13/cobra"

    "evalarena-cli/internal/dataaccess"
    "evalarena-cli/internal/httpclient"
)

func init() {
    pingCmd := &cobra.Command{
        Use:   "ping",
        Short: "Check API connectivity",
        Run: func(cmd *cobra.Command, args []string) {
            fmt.Println("Checking API connectivity...")
            ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
            defer cancel()
            client := httpclient.New()
            ok, msg := dataaccess.HealthCheck(ctx, client)
            if ok { fmt.Println("✓", msg) } else { fmt.Println("Error:", msg) }
        },
    }
    RegisterCommand(pingCmd)
}



