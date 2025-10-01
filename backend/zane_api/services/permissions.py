from typing import Optional
from django.contrib.auth import get_user_model
from django.db.models import QuerySet, Q
from ..models import Project, ProjectMember

User = get_user_model()


class ProjectPermissionService:
    """
    Service class for handling project-level permissions and role-based access control.
    
    This service provides methods to check user permissions, retrieve user roles,
    and filter projects based on user access rights.
    """
    
    # Permission definitions based on roles
    ROLE_PERMISSIONS = {
        ProjectMember.Role.OWNER: {
            'view_project',
            'manage_members',
            'delete_project',
            'create_services',
            'modify_services',
            'deploy_services',
            'view_logs',
            'manage_environments',
            'manage_volumes',
            'manage_configs',
            'manage_project_settings',
        },
        ProjectMember.Role.ADMIN: {
            'view_project',
            'create_services',
            'modify_services',
            'deploy_services',
            'view_logs',
            'manage_environments',
            'manage_volumes',
            'manage_configs',
        },
        ProjectMember.Role.DEVELOPER: {
            'view_project',
            'deploy_services',
            'view_logs',
        },
        ProjectMember.Role.VIEWER: {
            'view_project',
            'view_logs',
        },
    }
    
    @classmethod
    def has_permission(cls, user: User, project: Project, permission: str) -> bool:
        """
        Check if a user has a specific permission for a project.
        
        Args:
            user: The user to check permissions for
            project: The project to check permissions on
            permission: The permission string to check (e.g., 'view_project', 'manage_members')
            
        Returns:
            bool: True if the user has the permission, False otherwise
        """
        if not user or not user.is_authenticated:
            return False
            
        # Check if user is the original owner (backward compatibility)
        if project.owner == user:
            return permission in cls.ROLE_PERMISSIONS[ProjectMember.Role.OWNER]
        
        # Check project membership
        user_role = cls.get_user_role(user, project)
        if not user_role:
            return False
            
        return permission in cls.ROLE_PERMISSIONS.get(user_role, set())
    
    @classmethod
    def get_user_role(cls, user: User, project: Project) -> Optional[str]:
        """
        Get the user's role in a specific project.
        
        Args:
            user: The user to get the role for
            project: The project to check the role in
            
        Returns:
            Optional[str]: The user's role in the project, or None if not a member
        """
        if not user or not user.is_authenticated:
            return None
            
        # Check if user is the original owner (backward compatibility)
        if project.owner == user:
            return ProjectMember.Role.OWNER
            
        # Check project membership
        try:
            member = ProjectMember.objects.get(project=project, user=user)
            return member.role
        except ProjectMember.DoesNotExist:
            return None
    
    @classmethod
    def get_accessible_projects(cls, user: User) -> QuerySet[Project]:
        """
        Get all projects that a user has access to.
        
        Args:
            user: The user to get accessible projects for
            
        Returns:
            QuerySet[Project]: QuerySet of projects the user can access
        """
        if not user or not user.is_authenticated:
            return Project.objects.none()
        
        # Get projects where user is owner or a member
        return Project.objects.filter(
            Q(owner=user) | Q(members__user=user)
        ).distinct()
    
    @classmethod
    def can_manage_members(cls, user: User, project: Project) -> bool:
        """
        Check if a user can manage members for a project.
        Only owners can manage members.
        
        Args:
            user: The user to check
            project: The project to check
            
        Returns:
            bool: True if user can manage members, False otherwise
        """
        return cls.has_permission(user, project, 'manage_members')
    
    @classmethod
    def can_delete_project(cls, user: User, project: Project) -> bool:
        """
        Check if a user can delete a project.
        Only owners can delete projects.
        
        Args:
            user: The user to check
            project: The project to check
            
        Returns:
            bool: True if user can delete project, False otherwise
        """
        return cls.has_permission(user, project, 'delete_project')
    
    @classmethod
    def can_modify_services(cls, user: User, project: Project) -> bool:
        """
        Check if a user can create or modify services in a project.
        Owners and Admins can modify services.
        
        Args:
            user: The user to check
            project: The project to check
            
        Returns:
            bool: True if user can modify services, False otherwise
        """
        return (
            cls.has_permission(user, project, 'create_services') or
            cls.has_permission(user, project, 'modify_services')
        )
    
    @classmethod
    def can_deploy_services(cls, user: User, project: Project) -> bool:
        """
        Check if a user can deploy services in a project.
        Owners, Admins, and Developers can deploy services.
        
        Args:
            user: The user to check
            project: The project to check
            
        Returns:
            bool: True if user can deploy services, False otherwise
        """
        return cls.has_permission(user, project, 'deploy_services')
    
    @classmethod
    def can_view_logs(cls, user: User, project: Project) -> bool:
        """
        Check if a user can view logs for a project.
        All roles can view logs.
        
        Args:
            user: The user to check
            project: The project to check
            
        Returns:
            bool: True if user can view logs, False otherwise
        """
        return cls.has_permission(user, project, 'view_logs')
    
    @classmethod
    def get_project_members(cls, project: Project) -> QuerySet[ProjectMember]:
        """
        Get all members of a project, including the original owner.
        
        Args:
            project: The project to get members for
            
        Returns:
            QuerySet[ProjectMember]: QuerySet of project members
        """
        return ProjectMember.objects.filter(project=project).select_related('user')
    
    @classmethod
    def is_project_member(cls, user: User, project: Project) -> bool:
        """
        Check if a user is a member of a project (including original owner).
        
        Args:
            user: The user to check
            project: The project to check
            
        Returns:
            bool: True if user is a member, False otherwise
        """
        if not user or not user.is_authenticated:
            return False
            
        # Check if user is the original owner (backward compatibility)
        if project.owner == user:
            return True
            
        # Check project membership
        return ProjectMember.objects.filter(project=project, user=user).exists()