package dataaccess

import (
	"context"
	"fmt"
	"net/url"
	"sort"
	"strings"

	"evalarena-cli/internal/httpclient"
	"evalarena-cli/internal/models"
)

type ModelType string

const (
	ModelAll   ModelType = "all"
	ModelSmall ModelType = "small"
	ModelVLM   ModelType = "vlm"
	ModelChat  ModelType = "chat"
)

var endpointMap = map[ModelType]string{
	ModelAll:   "/api/models/",
	ModelSmall: "/api/small-models/",
	ModelVLM:   "/api/vlm-models/",
	ModelChat:  "/api/chat/models/",
}

func FetchModels(ctx context.Context, client *httpclient.Client, modelType ModelType, sortBy, order string, page, limit *int, bypassCache bool) ([]models.FullModel, error) {
	endpoint, ok := endpointMap[modelType]
	if !ok {
		return nil, fmt.Errorf("invalid model type: %s", modelType)
	}
	params := url.Values{}
	if sortBy != "" {
		params.Set("sortBy", sortBy)
	}
	if order != "" {
		params.Set("order", order)
	}

	var raw any
	if err := client.GetJSON(ctx, endpoint, params, &raw); err != nil {
		return nil, err
	}
	list := parseModels(raw)
	// client-side pagination
	if page != nil && limit != nil && *limit > 0 {
		start := (*page - 1) * (*limit)
		if start < 0 {
			start = 0
		}
		end := start + *limit
		if start >= len(list) {
			return []models.FullModel{}, nil
		}
		if end > len(list) {
			end = len(list)
		}
		list = list[start:end]
	} else if limit != nil && *limit > 0 {
		if *limit < len(list) {
			list = list[:*limit]
		}
	}
	return list, nil
}

func FetchModelByID(ctx context.Context, client *httpclient.Client, modelType ModelType, id string) (*models.FullModel, error) {
	endpoint, ok := endpointMap[modelType]
	if !ok {
		return nil, fmt.Errorf("invalid model type: %s", modelType)
	}
	var out models.FullModel
	if err := client.GetJSON(ctx, endpoint+id+"/", nil, &out); err != nil {
		return nil, err
	}
	return &out, nil
}

func SearchModelsByName(ctx context.Context, client *httpclient.Client, name string, modelType ModelType, fuzzy bool) ([]models.FullModel, error) {
	list, err := FetchModels(ctx, client, modelType, "name", "asc", nil, nil, false)
	if err != nil {
		return nil, err
	}
	needle := strings.ToLower(name)
	var result []models.FullModel
	for _, m := range list {
		lower := strings.ToLower(m.Name())
		if fuzzy {
			if strings.Contains(lower, needle) || strings.Contains(needle, lower) || strings.Contains(lower, strings.ReplaceAll(needle, "-", " ")) || strings.Contains(lower, strings.ReplaceAll(needle, " ", "-")) {
				result = append(result, m)
			}
		} else {
			if lower == needle {
				result = append(result, m)
			}
		}
	}
	return result, nil
}

func GetAllBenchmarkKeys(ctx context.Context, client *httpclient.Client, modelType ModelType) ([]string, error) {
	limit := 50
	list, err := FetchModels(ctx, client, modelType, "name", "asc", nil, &limit, false)
	if err != nil {
		return nil, err
	}
	set := map[string]struct{}{}
	for _, m := range list {
		for k := range m.AllBenchmarks() {
			set[k] = struct{}{}
		}
	}
	keys := make([]string, 0, len(set))
	for k := range set {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys, nil
}

func HealthCheck(ctx context.Context, client *httpclient.Client) (bool, string) {
	// Try ping first
	if code, err := client.GetStatus(ctx, "/api/ping/"); err == nil && code >= 200 && code < 300 {
		return true, "API is healthy"
	}
	// Fallback to models
	params := url.Values{"limit": []string{"1"}}
	var raw any
	if err := client.GetJSON(ctx, "/api/models/", params, &raw); err == nil {
		if arr, ok := raw.([]any); ok {
			return true, fmt.Sprintf("API is healthy (%d models sample)", len(arr))
		}
		return true, "API is healthy"
	}
	return false, "API error"
}

func parseModels(raw any) []models.FullModel {
	switch v := raw.(type) {
	case []any:
		res := make([]models.FullModel, 0, len(v))
		for _, it := range v {
			if m, ok := it.(map[string]any); ok {
				res = append(res, models.FullModel(m))
			}
		}
		return res
	case map[string]any:
		if data, ok := v["data"].([]any); ok {
			res := make([]models.FullModel, 0, len(data))
			for _, it := range data {
				if m, ok := it.(map[string]any); ok {
					res = append(res, models.FullModel(m))
				}
			}
			return res
		}
		// Sometimes API returns raw list
		res := []models.FullModel{}
		for _, it := range v {
			if m, ok := it.(map[string]any); ok {
				res = append(res, models.FullModel(m))
			}
		}
		return res
	default:
		return []models.FullModel{}
	}
}
