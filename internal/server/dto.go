package server

import (
	"encoding/json"

	"proofline/internal/config"
	"proofline/internal/domain"
)

// Request payloads

type CreateProjectRequest struct {
	ID          string  `json:"id"`
	Description *string `json:"description,omitempty"`
}

type TaskValidationRequest struct {
	Mode      string   `json:"mode,omitempty" enum:"none,all,any,threshold" example:"all"`
	Require   []string `json:"require,omitempty" example:"[\"ci.passed\",\"review.approved\"]"`
	Threshold *int     `json:"threshold,omitempty" example:"2"`
}

type TaskPolicyRequest struct {
	Preset string `json:"preset,omitempty" example:"feature.default"`
}

type CreateTaskRequest struct {
	ID          *string                `json:"id,omitempty" example:"task-auth-1"`
	IterationID *string                `json:"iteration_id,omitempty" example:"iter-1"`
	ParentID    *string                `json:"parent_id,omitempty" example:"task-epic"`
	Type        string                 `json:"type" enum:"technical,feature,bug,docs,chore" example:"feature"`
	Title       string                 `json:"title" example:"Ship authentication"`
	Description *string                `json:"description,omitempty" example:"Implement login and SSO flows"`
	AssigneeID  *string                `json:"assignee_id,omitempty" example:"dev-1"`
	DependsOn   []string               `json:"depends_on,omitempty" example:"[\"task-seed\"]"`
	Policy      *TaskPolicyRequest     `json:"policy,omitempty"`
	Validation  *TaskValidationRequest `json:"validation,omitempty"`
	WorkProof   map[string]any         `json:"work_proof,omitempty" example:"{\"pr\":123}"`
}

type UpdateTaskValidationRequest struct {
	Mode      *string  `json:"mode,omitempty" enum:"none,all,any,threshold"`
	Require   []string `json:"require,omitempty"`
	Threshold *int     `json:"threshold,omitempty"`
}

type UpdateTaskRequest struct {
	Status          *string                      `json:"status,omitempty" enum:"planned,in_progress,review,done,rejected,canceled"`
	AssigneeID      *string                      `json:"assignee_id,omitempty"`
	AddDependsOn    []string                     `json:"add_depends_on,omitempty"`
	RemoveDependsOn []string                     `json:"remove_depends_on,omitempty"`
	ParentID        *string                      `json:"parent_id,omitempty"`
	WorkProof       *map[string]any              `json:"work_proof,omitempty"`
	Validation      *UpdateTaskValidationRequest `json:"validation,omitempty"`
}

type CompleteTaskRequest struct {
	WorkProof map[string]any `json:"work_proof"`
}

type CreateIterationRequest struct {
	ID   string `json:"id"`
	Goal string `json:"goal"`
}

type SetIterationStatusRequest struct {
	Status string `json:"status" enum:"pending,running,delivered,validated,rejected"`
}

type CreateDecisionRequest struct {
	ID           string         `json:"id" example:"dec-1"`
	Title        string         `json:"title" example:"Choose runtime"`
	Decision     string         `json:"decision" example:"Adopt Go for backend"`
	DeciderID    string         `json:"decider_id" example:"cto-1"`
	Context      map[string]any `json:"context,omitempty"`
	Rationale    []string       `json:"rationale,omitempty" example:"[\"Team experience\",\"Ecosystem support\"]"`
	Alternatives []string       `json:"alternatives,omitempty" example:"[\"Rust\",\"NodeJS\"]"`
}

type CreateAttestationRequest struct {
	ID         *string        `json:"id,omitempty" example:"att-1"`
	EntityKind string         `json:"entity_kind" enum:"project,iteration,task,decision" example:"task"`
	EntityID   string         `json:"entity_id" example:"task-auth-1"`
	Kind       string         `json:"kind" example:"review.approved"`
	TS         *string        `json:"ts,omitempty" format:"date-time" example:"2024-05-01T10:00:00Z"`
	Payload    map[string]any `json:"payload,omitempty" example:"{\"note\":\"LGTM\"}"`
}

// Response payloads

type ProjectResponse struct {
	ID          string `json:"id"`
	Kind        string `json:"kind"`
	Status      string `json:"status"`
	Description string `json:"description,omitempty"`
	CreatedAt   string `json:"created_at" format:"date-time"`
}

type IterationResponse struct {
	ID        string `json:"id"`
	ProjectID string `json:"project_id"`
	Goal      string `json:"goal"`
	Status    string `json:"status" enum:"pending,running,delivered,validated,rejected"`
	CreatedAt string `json:"created_at" format:"date-time"`
}

type TaskResponse struct {
	ID                   string         `json:"id" example:"task-auth-1"`
	ProjectID            string         `json:"project_id" example:"proofline"`
	IterationID          *string        `json:"iteration_id,omitempty" example:"iter-1"`
	ParentID             *string        `json:"parent_id,omitempty" example:"task-epic"`
	Type                 string         `json:"type" enum:"technical,feature,bug,docs,chore" example:"feature"`
	Title                string         `json:"title" example:"Ship authentication"`
	Description          string         `json:"description,omitempty" example:"Implement login and SSO flows"`
	Status               string         `json:"status" enum:"planned,in_progress,review,done,rejected,canceled" example:"planned"`
	AssigneeID           *string        `json:"assignee_id,omitempty" example:"dev-1"`
	WorkProof            map[string]any `json:"work_proof,omitempty" example:"{\"pr\":123}"`
	ValidationMode       string         `json:"validation_mode" enum:"none,all,any,threshold" example:"all"`
	RequiredAttestations []string       `json:"required_attestations" example:"[\"ci.passed\",\"review.approved\"]"`
	RequiredThreshold    *int           `json:"required_threshold,omitempty" example:"2"`
	DependsOn            []string       `json:"depends_on" example:"[]"`
	CreatedAt            string         `json:"created_at" format:"date-time" example:"2024-05-01T09:00:00Z"`
	UpdatedAt            string         `json:"updated_at" format:"date-time" example:"2024-05-01T09:05:00Z"`
	CompletedAt          *string        `json:"completed_at" format:"date-time" example:"2024-05-02T10:00:00Z"`
}

type DecisionResponse struct {
	ID           string         `json:"id"`
	ProjectID    string         `json:"project_id"`
	Title        string         `json:"title"`
	Decision     string         `json:"decision"`
	DeciderID    string         `json:"decider_id"`
	Context      map[string]any `json:"context,omitempty"`
	Rationale    []string       `json:"rationale"`
	Alternatives []string       `json:"alternatives"`
	CreatedAt    string         `json:"created_at" format:"date-time"`
}

type LeaseResponse struct {
	TaskID     string `json:"task_id"`
	OwnerID    string `json:"owner_id"`
	AcquiredAt string `json:"acquired_at" format:"date-time"`
	ExpiresAt  string `json:"expires_at" format:"date-time"`
}

type AttestationResponse struct {
	ID         string         `json:"id"`
	ProjectID  string         `json:"project_id"`
	EntityKind string         `json:"entity_kind" enum:"project,iteration,task,decision"`
	EntityID   string         `json:"entity_id"`
	Kind       string         `json:"kind"`
	ActorID    string         `json:"actor_id"`
	TS         string         `json:"ts" format:"date-time"`
	Payload    map[string]any `json:"payload,omitempty"`
}

type EventResponse struct {
	ID         int64          `json:"id"`
	TS         string         `json:"ts" format:"date-time"`
	Type       string         `json:"type"`
	ProjectID  string         `json:"project_id,omitempty"`
	EntityKind string         `json:"entity_kind" enum:"project,iteration,task,decision,rbac"`
	EntityID   string         `json:"entity_id,omitempty"`
	ActorID    string         `json:"actor_id"`
	Payload    map[string]any `json:"payload"`
}

type ValidationStatusResponse struct {
	Mode      string   `json:"mode" enum:"none,all,any,threshold" example:"all"`
	Required  []string `json:"required" example:"[\"ci.passed\",\"review.approved\"]"`
	Threshold *int     `json:"threshold,omitempty" example:"2"`
	Present   []string `json:"present" example:"[\"ci.passed\"]"`
	Missing   []string `json:"missing" example:"[\"review.approved\"]"`
	Satisfied bool     `json:"satisfied" example:"false"`
}

type ProjectConfigResponse struct {
	Project      projectConfigSection     `json:"project"`
	Attestations attestationConfigSection `json:"attestations"`
	Policies     policyConfigSection      `json:"policies"`
}

type projectConfigSection struct {
	ID   string `json:"id"`
	Kind string `json:"kind"`
}

type attestationConfigSection struct {
	Catalog map[string]struct {
		Description string `json:"description"`
	} `json:"catalog"`
}

type policyConfigSection struct {
	Presets  map[string]policyPresetResponse `json:"presets"`
	Defaults struct {
		Task      map[string]string `json:"task"`
		Iteration struct {
			Validation struct {
				Require string `json:"require"`
			} `json:"validation"`
		} `json:"iteration"`
	} `json:"defaults"`
}

type policyPresetResponse struct {
	Mode      string   `json:"mode" enum:"none,all,any,threshold"`
	Require   []string `json:"require"`
	Threshold *int     `json:"threshold,omitempty"`
}

type paginatedTasks struct {
	Items      []TaskResponse `json:"items"`
	NextCursor string         `json:"next_cursor,omitempty"`
}

type paginatedIterations struct {
	Items      []IterationResponse `json:"items"`
	NextCursor string              `json:"next_cursor,omitempty"`
}

type paginatedAttestations struct {
	Items      []AttestationResponse `json:"items"`
	NextCursor string                `json:"next_cursor,omitempty"`
}

type paginatedEvents struct {
	Items      []EventResponse `json:"items"`
	NextCursor string          `json:"next_cursor,omitempty"`
}

type RoleChangeRequest struct {
	ActorID string `json:"actor_id"`
	RoleID  string `json:"role_id"`
}

type AttestationAuthorityRequest struct {
	Kind   string `json:"kind"`
	RoleID string `json:"role_id"`
}

type WhoAmIResponse struct {
	ActorID     string   `json:"actor_id"`
	Roles       []string `json:"roles"`
	Permissions []string `json:"permissions"`
}

// Conversion helpers

func projectResponse(p domain.Project) ProjectResponse {
	return ProjectResponse(p)
}

func iterationResponse(it domain.Iteration) IterationResponse {
	return IterationResponse(it)
}

func taskResponse(t domain.Task) TaskResponse {
	req := decodeStringSlice(t.RequiredAttestationsJSON)
	wp := decodeJSONMap(t.WorkProofJSON)
	return TaskResponse{
		ID:                   t.ID,
		ProjectID:            t.ProjectID,
		IterationID:          t.IterationID,
		ParentID:             t.ParentID,
		Type:                 t.Type,
		Title:                t.Title,
		Description:          t.Description,
		Status:               t.Status,
		AssigneeID:           t.AssigneeID,
		WorkProof:            wp,
		ValidationMode:       defaultMode(t.ValidationMode),
		RequiredAttestations: nonNilSlice(req),
		RequiredThreshold:    t.RequiredThreshold,
		DependsOn:            nonNilSlice(t.DependsOn),
		CreatedAt:            t.CreatedAt,
		UpdatedAt:            t.UpdatedAt,
		CompletedAt:          t.CompletedAt,
	}
}

func decisionResponse(d domain.Decision) DecisionResponse {
	return DecisionResponse{
		ID:           d.ID,
		ProjectID:    d.ProjectID,
		Title:        d.Title,
		Decision:     d.Decision,
		DeciderID:    d.DeciderID,
		Context:      decodeJSONMap(strPtr(d.ContextJSON)),
		Rationale:    nonNilSlice(decodeStringSlice(strPtr(d.RationaleJSON))),
		Alternatives: nonNilSlice(decodeStringSlice(strPtr(d.AlternativesJSON))),
		CreatedAt:    d.CreatedAt,
	}
}

func attestationResponse(a domain.Attestation) AttestationResponse {
	return AttestationResponse{
		ID:         a.ID,
		ProjectID:  a.ProjectID,
		EntityKind: a.EntityKind,
		EntityID:   a.EntityID,
		Kind:       a.Kind,
		ActorID:    a.ActorID,
		TS:         a.TS,
		Payload:    decodeJSONMap(strPtr(a.PayloadJSON)),
	}
}

func eventResponse(e domain.Event) EventResponse {
	return EventResponse{
		ID:         e.ID,
		TS:         e.TS,
		Type:       e.Type,
		ProjectID:  e.ProjectID,
		EntityKind: e.EntityKind,
		EntityID:   e.EntityID,
		ActorID:    e.ActorID,
		Payload:    decodeJSONMap(strPtr(e.Payload)),
	}
}

func configResponse(cfg *config.Config) ProjectConfigResponse {
	res := ProjectConfigResponse{
		Project: projectConfigSection{
			ID:   cfg.Project.ID,
			Kind: cfg.Project.Kind,
		},
		Attestations: attestationConfigSection{
			Catalog: map[string]struct {
				Description string `json:"description"`
			}{},
		},
		Policies: policyConfigSection{
			Presets: map[string]policyPresetResponse{},
		},
	}
	for k, v := range cfg.Attestations.Catalog {
		res.Attestations.Catalog[k] = struct {
			Description string `json:"description"`
		}{Description: v.Description}
	}
	for name, preset := range cfg.Policies.Presets {
		res.Policies.Presets[name] = policyPresetResponse{
			Mode:      preset.Mode,
			Require:   nonNilSlice(preset.Require),
			Threshold: preset.Threshold,
		}
	}
	res.Policies.Defaults.Task = cfg.Policies.Defaults.Task
	res.Policies.Defaults.Iteration.Validation.Require = cfg.Policies.Defaults.Iteration.Validation.Require
	return res
}

// JSON helpers

func decodeJSONMap(raw *string) map[string]any {
	if raw == nil || *raw == "" {
		return nil
	}
	var tmp any
	if err := json.Unmarshal([]byte(*raw), &tmp); err != nil {
		return nil
	}
	if obj, ok := tmp.(map[string]any); ok {
		return obj
	}
	return nil
}

func decodeStringSlice(raw *string) []string {
	if raw == nil || *raw == "" {
		return []string{}
	}
	var arr []string
	if err := json.Unmarshal([]byte(*raw), &arr); err != nil {
		return []string{}
	}
	return arr
}

func nonNilSlice[T any](in []T) []T {
	if in == nil {
		return []T{}
	}
	return in
}

func defaultMode(mode string) string {
	if mode == "" {
		return "none"
	}
	return mode
}

func strPtr(in string) *string {
	return &in
}
