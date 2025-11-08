package cmd

import (
    "bufio"
    "context"
    "fmt"
    "io"
    "net/http"
    "sort"
    "strings"
    "sync"
    "time"

    "github.com/spf13/cobra"

    "evalarena-cli/internal/auth"
    "evalarena-cli/internal/config"
    "evalarena-cli/internal/httpclient"
)

type chatModel struct { ID, Name, Creator string }

func init() {
    chatCmd := &cobra.Command{
        Use:   "chat",
        Short: "Chat with one or multiple models and compare responses",
        RunE: func(cmd *cobra.Command, args []string) error {
            cfg := config.Load()
            list, _ := cmd.Flags().GetBool("list")
            setModels, _ := cmd.Flags().GetString("set-models")
            clearModels, _ := cmd.Flags().GetBool("clear-models")
            modelsCSV, _ := cmd.Flags().GetString("models")
            prompt, _ := cmd.Flags().GetString("prompt")
            noProgress, _ := cmd.Flags().GetBool("no-progress")

            if list {
                avail, err := getAvailableChatModels()
                if err != nil { return err }
                fmt.Println("Available Chat Models:")
                for _, m := range avail { fmt.Printf("  %s  %s  (%s)\n", m.ID, m.Name, m.Creator) }
                return nil
            }

            if setModels != "" || clearModels {
                value := ""
                if !clearModels { value = setModels }
                if err := config.SaveEnv("EVALARENA_CHAT_DEFAULT_MODELS", value); err != nil { return err }
                if clearModels { fmt.Println("Cleared default chat models") } else { fmt.Println("Set default chat models:", value) }
                return nil
            }

            if prompt == "" {
                return fmt.Errorf("please provide a prompt with --prompt")
            }

            if modelsCSV == "" && len(cfg.Chat.DefaultModels) > 0 {
                modelsCSV = strings.Join(cfg.Chat.DefaultModels, ",")
            }
            if modelsCSV == "" { return fmt.Errorf("no chat models specified; use --models or --set-models") }

            ids := splitCSV(modelsCSV)
            if len(ids) == 0 { return fmt.Errorf("no valid model IDs provided") }
            if len(ids) > 4 { return fmt.Errorf("maximum 4 models supported for comparison") }

            return chatWithMultipleModels(prompt, ids, !noProgress)
        },
    }
    chatCmd.Flags().StringP("prompt", "p", "", "Prompt to send to the chat models")
    chatCmd.Flags().StringP("models", "m", "", "Comma-separated list of model IDs to compare")
    chatCmd.Flags().String("set-models", "", "Persist default chat models (comma-separated). Use --clear-models to remove.")
    chatCmd.Flags().Bool("clear-models", false, "Clear default chat models from config")
    chatCmd.Flags().Bool("list", false, "List available chat models")
    chatCmd.Flags().Bool("no-progress", false, "Disable live progress display")
    RegisterCommand(chatCmd)
}

func getAvailableChatModels() ([]chatModel, error) {
    cfg := config.Load()
    ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+5)*time.Second)
    defer cancel()
    client := httpclient.New()
    var raw []map[string]any
    if err := client.GetJSON(ctx, "/api/chat/models/", nil, &raw); err != nil { return nil, err }
    out := make([]chatModel, 0, len(raw))
    for _, m := range raw {
        id, _ := m["id"].(string)
        name, _ := m["name"].(string)
        creator, _ := m["creator"].(string)
        out = append(out, chatModel{ID: id, Name: name, Creator: creator})
    }
    sort.Slice(out, func(i, j int) bool { return out[i].Name < out[j].Name })
    return out, nil
}

func chatWithMultipleModels(prompt string, modelIDs []string, showProgress bool) error {
    cfg := config.Load()
    avail, err := getAvailableChatModels()
    if err != nil { return err }
    lookup := map[string]chatModel{}
    for _, m := range avail { lookup[m.ID] = m }
    for _, id := range modelIDs { if _, ok := lookup[id]; !ok { return fmt.Errorf("model '%s' not found; run 'evalarena chat --list'", id) } }

    ctx, cancel := context.WithTimeout(context.Background(), time.Duration(cfg.TimeoutSeconds+45)*time.Second)
    defer cancel()
    client := httpclient.New()

    type result struct { id string; text string; err error }
    outCh := make(chan result)
    var wg sync.WaitGroup
    wg.Add(len(modelIDs))
    for _, id := range modelIDs {
        go func(modelID string) {
            defer wg.Done()
            payload := map[string]any{
                "messages": []map[string]string{{"role": "user", "content": prompt}},
                "selectedModel": modelID,
            }
            resp, err := client.PostStream(ctx, "/api/chat/chat/", payload, func(r *http.Request) {
                // add auth header if available
                for k, vals := range auth.GetAuthHeader() { for _, v := range vals { r.Header.Add(k, v) } }
                r.Header.Set("Accept", "text/plain, application/json")
            })
            if err != nil { outCh <- result{id: modelID, err: err}; return }
            defer resp.Body.Close()
            var builder strings.Builder
            reader := bufio.NewReader(resp.Body)
            buf := make([]byte, 2048)
            for {
                n, readErr := reader.Read(buf)
                if n > 0 {
                    chunk := string(buf[:n])
                    builder.WriteString(chunk)
                    if showProgress {
                        // stream chunked output with prefix
                        fmt.Printf("[%s] %s", modelID, chunk)
                    }
                }
                if readErr != nil {
                    if readErr == io.EOF { break }
                    outCh <- result{id: modelID, err: readErr}
                    return
                }
            }
            outCh <- result{id: modelID, text: builder.String(), err: nil}
        }(id)
    }

    go func() { wg.Wait(); close(outCh) }()

    // collect results
    results := map[string]string{}
    var haveErr error
    for r := range outCh {
        if r.err != nil { haveErr = r.err; continue }
        results[r.id] = r.text
    }

    // final pretty output
    fmt.Println("\n================ FINAL RESULTS ================")
    for i, id := range modelIDs {
        m := lookup[id]
        fmt.Printf("\n%02d. %s (%s)\n%s\n", i+1, m.Name, m.Creator, strings.Repeat("-", 60))
        if s := results[id]; strings.TrimSpace(s) != "" {
            fmt.Println(s)
        } else {
            fmt.Println("(no response)")
        }
    }
    return haveErr
}


