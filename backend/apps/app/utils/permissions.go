package utils

import (
	"github.com/spectrumwebco/agent_runtime/pkg/djangogo/core"
)

type IsOrganizationMember struct {
	core.BasePermission
}

func NewIsOrganizationMember() *IsOrganizationMember {
	return &IsOrganizationMember{
		BasePermission: core.NewBasePermission(),
	}
}

func (p *IsOrganizationMember) HasObjectPermission(request *core.Request, view interface{}, obj interface{}) bool {
	user := request.User
	
	if user.IsSuperuser() {
		return true
	}
	
	if org, ok := core.GetObjectAttr(obj, "organization"); ok {
		return core.UserInQuerySet(user, core.GetQuerySet(org, "users"))
	}
	
	return false
}

type IsOrganizationAdmin struct {
	core.BasePermission
}

func NewIsOrganizationAdmin() *IsOrganizationAdmin {
	return &IsOrganizationAdmin{
		BasePermission: core.NewBasePermission(),
	}
}

func (p *IsOrganizationAdmin) HasObjectPermission(request *core.Request, view interface{}, obj interface{}) bool {
	user := request.User
	
	if user.IsSuperuser() {
		return true
	}
	
	if org, ok := core.GetObjectAttr(obj, "organization"); ok {
		return core.UserInQuerySet(user, core.GetQuerySet(org, "admins"))
	}
	
	return false
}

type IsWorkspaceMember struct {
	core.BasePermission
}

func NewIsWorkspaceMember() *IsWorkspaceMember {
	return &IsWorkspaceMember{
		BasePermission: core.NewBasePermission(),
	}
}

func (p *IsWorkspaceMember) HasObjectPermission(request *core.Request, view interface{}, obj interface{}) bool {
	user := request.User
	
	if user.IsSuperuser() {
		return true
	}
	
	if workspace, ok := core.GetObjectAttr(obj, "workspace"); ok {
		return core.UserInQuerySet(user, core.GetQuerySet(workspace, "members"))
	}
	
	return false
}

type IsWorkspaceAdmin struct {
	core.BasePermission
}

func NewIsWorkspaceAdmin() *IsWorkspaceAdmin {
	return &IsWorkspaceAdmin{
		BasePermission: core.NewBasePermission(),
	}
}

func (p *IsWorkspaceAdmin) HasObjectPermission(request *core.Request, view interface{}, obj interface{}) bool {
	user := request.User
	
	if user.IsSuperuser() {
		return true
	}
	
	if workspace, ok := core.GetObjectAttr(obj, "workspace"); ok {
		return core.UserInQuerySet(user, core.GetQuerySet(workspace, "admins"))
	}
	
	return false
}

type IsOwner struct {
	core.BasePermission
}

func NewIsOwner() *IsOwner {
	return &IsOwner{
		BasePermission: core.NewBasePermission(),
	}
}

func (p *IsOwner) HasObjectPermission(request *core.Request, view interface{}, obj interface{}) bool {
	user := request.User
	
	if user.IsSuperuser() {
		return true
	}
	
	if createdBy, ok := core.GetObjectAttr(obj, "created_by"); ok {
		return core.ObjectsEqual(createdBy, user)
	}
	
	if objUser, ok := core.GetObjectAttr(obj, "user"); ok {
		return core.ObjectsEqual(objUser, user)
	}
	
	return false
}

type ReadOnly struct {
	core.BasePermission
}

func NewReadOnly() *ReadOnly {
	return &ReadOnly{
		BasePermission: core.NewBasePermission(),
	}
}

func (p *ReadOnly) HasPermission(request *core.Request, view interface{}) bool {
	return core.IsReadOnlyMethod(request.Method)
}

type HasAPIKey struct {
	core.BasePermission
}

func NewHasAPIKey() *HasAPIKey {
	return &HasAPIKey{
		BasePermission: core.NewBasePermission(),
	}
}

func (p *HasAPIKey) HasPermission(request *core.Request, view interface{}) bool {
	apiKey := p.getAPIKey(request)
	
	if apiKey == "" {
		return false
	}
	
	result, err := core.CallPythonFunction("apps.app.models.core", "ApiKey.objects.active().filter", []interface{}{
		map[string]interface{}{"key": apiKey},
	})
	
	if err != nil {
		return false
	}
	
	keys, ok := result.([]interface{})
	if !ok || len(keys) == 0 {
		return false
	}
	
	_, err = core.CallPythonFunction("apps.app.models.core", "ApiKey.objects.get", []interface{}{
		map[string]interface{}{"key": apiKey},
		"update_last_used",
	})
	
	request.SetContextValue("api_key", keys[0])
	
	return true
}

func (p *HasAPIKey) getAPIKey(request *core.Request) string {
	apiKey := request.GetHeader("X-API-Key")
	if apiKey != "" {
		return apiKey
	}
	
	apiKey = request.GetQueryParam("api_key")
	if apiKey != "" {
		return apiKey
	}
	
	return ""
}

func init() {
	core.RegisterPermission("IsOrganizationMember", NewIsOrganizationMember())
	core.RegisterPermission("IsOrganizationAdmin", NewIsOrganizationAdmin())
	core.RegisterPermission("IsWorkspaceMember", NewIsWorkspaceMember())
	core.RegisterPermission("IsWorkspaceAdmin", NewIsWorkspaceAdmin())
	core.RegisterPermission("IsOwner", NewIsOwner())
	core.RegisterPermission("ReadOnly", NewReadOnly())
	core.RegisterPermission("HasAPIKey", NewHasAPIKey())
}
