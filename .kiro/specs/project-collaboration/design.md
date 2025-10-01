# Design Document

## Overview

This design implements a role-based access control (RBAC) system for project collaboration in ZaneOps. The system will allow multiple users to collaborate on projects while maintaining security through granular permissions. The design extends the existing single-owner model to support multiple collaborators with different permission levels.

## Architecture

### Database Schema Changes

#### New Models

**ProjectMember Model**
```python
class ProjectMember(TimestampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="sent_invitations")
    
    class Role(models.TextChoices):
        OWNER = "OWNER", _("Owner")
        ADMIN = "ADMIN", _("Admin") 
        DEVELOPER = "DEVELOPER", _("Developer")
        VIEWER = "VIEWER", _("Viewer")
    
    class Meta:
        unique_together = ["project", "user"]
```

**ProjectInvitation Model**
```python
class ProjectInvitation(TimestampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ProjectMember.Role.choices)
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True)
    declined_at = models.DateTimeField(null=True)
    
    class Meta:
        unique_together = ["project", "email"]
```

#### Modified Models

**Project Model Changes**
- Keep existing `owner` field for backward compatibility
- Add `members` relationship through ProjectMember
- Add helper methods for permission checking

### Permission System

#### Role Definitions

| Role | Permissions |
|------|-------------|
| **Owner** | Full access: manage members, delete project, all admin/developer/viewer permissions |
| **Admin** | Manage services, deployments, environments, volumes, configs. Cannot manage members or delete project |
| **Developer** | Deploy services, view logs, manage own deployments. Cannot modify project settings |
| **Viewer** | Read-only access to project status, logs, and configurations |

#### Permission Matrix

| Action | Owner | Admin | Developer | Viewer |
|--------|-------|-------|-----------|--------|
| View project | ✓ | ✓ | ✓ | ✓ |
| Manage members | ✓ | ✗ | ✗ | ✗ |
| Delete project | ✓ | ✗ | ✗ | ✗ |
| Create/modify services | ✓ | ✓ | ✗ | ✗ |
| Deploy services | ✓ | ✓ | ✓ | ✗ |
| View logs | ✓ | ✓ | ✓ | ✓ |
| Manage environments | ✓ | ✓ | ✗ | ✗ |
| Manage volumes/configs | ✓ | ✓ | ✗ | ✗ |

## Components and Interfaces

### Permission Checking Service

```python
class ProjectPermissionService:
    @staticmethod
    def has_permission(user: User, project: Project, permission: str) -> bool:
        """Check if user has specific permission for project"""
        
    @staticmethod
    def get_user_role(user: User, project: Project) -> Optional[str]:
        """Get user's role in project"""
        
    @staticmethod
    def get_accessible_projects(user: User) -> QuerySet[Project]:
        """Get all projects user has access to"""
```

### Invitation Service

```python
class ProjectInvitationService:
    @staticmethod
    def send_invitation(project: Project, email: str, role: str, invited_by: User) -> ProjectInvitation:
        """Send project invitation to user"""
        
    @staticmethod
    def accept_invitation(token: str, user: User) -> ProjectMember:
        """Accept project invitation"""
        
    @staticmethod
    def decline_invitation(token: str) -> None:
        """Decline project invitation"""
```

### Updated Views and Serializers

#### ProjectsListAPIView Changes
- Modify `get_queryset()` to use `ProjectPermissionService.get_accessible_projects()`
- Update filtering logic to include projects where user is a member

#### New API Endpoints
- `POST /projects/{slug}/members/invite/` - Invite user to project
- `GET /projects/{slug}/members/` - List project members
- `PATCH /projects/{slug}/members/{user_id}/` - Update member role
- `DELETE /projects/{slug}/members/{user_id}/` - Remove member
- `POST /invitations/{token}/accept/` - Accept invitation
- `POST /invitations/{token}/decline/` - Decline invitation
- `GET /invitations/` - List user's pending invitations

## Data Models

### ProjectMember
- **id**: Primary key
- **project**: Foreign key to Project
- **user**: Foreign key to User
- **role**: Choice field (OWNER, ADMIN, DEVELOPER, VIEWER)
- **invited_by**: Foreign key to User who sent invitation
- **created_at/updated_at**: Timestamps

### ProjectInvitation
- **id**: Primary key
- **project**: Foreign key to Project
- **email**: Email address of invitee
- **role**: Intended role for invitee
- **invited_by**: Foreign key to User who sent invitation
- **token**: Unique token for invitation acceptance
- **expires_at**: Expiration timestamp
- **accepted_at**: Acceptance timestamp (nullable)
- **declined_at**: Decline timestamp (nullable)
- **created_at/updated_at**: Timestamps

## Error Handling

### Permission Denied Responses
- **403 Forbidden**: When user lacks permission for action
- **404 Not Found**: When user cannot access project (security through obscurity)

### Invitation Error Handling
- **400 Bad Request**: Invalid email, role, or expired invitation
- **409 Conflict**: User already member or invitation already exists
- **404 Not Found**: Invalid invitation token

### Validation Rules
- Email validation for invitations
- Role validation against allowed choices
- Invitation expiration checking
- Duplicate member prevention

## Testing Strategy

### Unit Tests
- **Permission Service Tests**: Verify role-based permission checking
- **Invitation Service Tests**: Test invitation lifecycle
- **Model Tests**: Validate constraints and relationships

### Integration Tests
- **API Endpoint Tests**: Test all new collaboration endpoints
- **Permission Integration Tests**: Verify permissions across different views
- **Invitation Flow Tests**: End-to-end invitation acceptance/decline

### Security Tests
- **Authorization Tests**: Verify users cannot access unauthorized projects
- **Token Security Tests**: Test invitation token security
- **Permission Escalation Tests**: Ensure users cannot escalate their own permissions

### Migration Data Integrity Tests
- **Backward Compatibility**: Ensure existing projects continue working
- **Owner Migration**: Verify existing owners become project members with OWNER role

## Migration Strategy

### Database Migration Steps
1. Create ProjectMember and ProjectInvitation tables
2. Migrate existing project owners to ProjectMember with OWNER role
3. Add indexes for performance optimization
4. Update foreign key constraints

### Code Migration Steps
1. Deploy new models and permission system
2. Update views to use new permission checking
3. Add new API endpoints for collaboration
4. Update frontend to support collaboration features

### Rollback Plan
- Keep existing `owner` field during transition period
- Implement feature flags for gradual rollout
- Maintain backward compatibility in API responses