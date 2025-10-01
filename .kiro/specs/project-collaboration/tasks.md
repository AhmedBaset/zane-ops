# Implementation Plan

- [x] 1. Create database models and migrations
  - Create ProjectMember and ProjectInvitation models with proper relationships and constraints
  - Generate Django migrations for the new models
  - Add database indexes for performance optimization
  - _Requirements: 1.1, 2.1, 3.1, 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 2. Implement permission checking service
  - Create ProjectPermissionService class with role-based permission methods
  - Implement has_permission method for granular permission checking
  - Add get_user_role method to retrieve user's role in a project
  - Create get_accessible_projects method for filtering user-accessible projects
  - Write unit tests for all permission checking logic
  - _Requirements: 3.3, 4.3, 5.3, 6.2, 6.3, 6.4, 6.5_

- [ ] 3. Create invitation management service
  - Implement ProjectInvitationService class for handling invitations
  - Add send_invitation method with email validation and token generation
  - Create accept_invitation method with token validation and member creation
  - Implement decline_invitation method with proper cleanup
  - Add invitation expiration checking and cleanup
  - Write unit tests for invitation lifecycle management
  - _Requirements: 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4. Update project model and add helper methods
  - Add members relationship to Project model through ProjectMember
  - Create helper methods for checking user permissions on projects
  - Add methods to get project members and their roles
  - Implement backward compatibility methods for existing owner field
  - Write unit tests for new Project model methods
  - _Requirements: 3.1, 4.1, 5.1_

- [ ] 5. Create serializers for collaboration features
  - Create ProjectMemberSerializer for member data representation
  - Implement ProjectInvitationSerializer for invitation data
  - Add InviteUserSerializer for invitation request validation
  - Create UpdateMemberRoleSerializer for role change requests
  - Write serializer validation tests
  - _Requirements: 1.1, 2.1, 3.1, 3.2_

- [x] 6. Update project views with permission checking
  - Modify ProjectsListAPIView.get_queryset to use ProjectPermissionService
  - Add permission checks to ProjectDetailsView methods (get, patch, delete)
  - Update ProjectServiceListAPIView to verify project access permissions
  - Implement proper error responses for permission denied scenarios
  - Write integration tests for updated views
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.4_

- [ ] 7. Create project member management API endpoints
  - Implement ProjectMembersListView for listing and inviting members
  - Create ProjectMemberDetailView for updating and removing members
  - Add proper permission checks (only owners can manage members)
  - Implement input validation and error handling
  - Write API endpoint tests for member management
  - _Requirements: 1.1, 1.2, 1.5, 3.1, 3.2, 3.3, 5.5_

- [ ] 8. Create invitation management API endpoints
  - Implement InvitationAcceptView for accepting invitations
  - Create InvitationDeclineView for declining invitations
  - Add UserInvitationsListView for listing user's pending invitations
  - Implement token validation and security measures
  - Write API endpoint tests for invitation management
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 9. Create data migration for existing projects
  - Write Django data migration to convert existing project owners to ProjectMembers
  - Ensure all existing projects have owner as OWNER role member
  - Add validation to ensure no data loss during migration
  - Create rollback migration for safety
  - Test migration with sample data
  - _Requirements: 5.1, 6.1_

- [ ] 10. Add URL routing for new API endpoints
  - Add URL patterns for member management endpoints
  - Create URL patterns for invitation management endpoints
  - Update project URLs to include collaboration routes
  - Ensure proper URL namespacing and organization
  - Test URL routing and endpoint accessibility
  - _Requirements: 1.1, 2.1, 3.1_

- [ ] 11. Implement audit logging for security
  - Add logging for member additions and removals
  - Create logs for role changes and permission modifications
  - Implement security event logging for suspicious activities
  - Add invitation acceptance/decline logging
  - Write tests for audit logging functionality
  - _Requirements: 3.5, 5.1, 5.4, 5.5_

- [x] 12. Update all project-related views with permission checking
  - Update environments.py views to use ProjectPermissionService instead of owner checks
  - Update docker_services.py views to use new permission system for project access
  - Update git_services.py views to replace owner filtering with member-based access
  - Update deployments.py views to use permission checking for project resources
  - Update logs.py views to verify project access through membership
  - Update metrics.py views to use new project access control
  - Replace all `Project.objects.get(slug=X, owner=request.user)` patterns with permission-based access
  - Ensure consistent error handling across all updated views
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 5.1, 5.4_

- [ ] 13. Create comprehensive integration tests
  - Write end-to-end tests for complete invitation workflow
  - Create tests for permission enforcement across all endpoints
  - Add tests for edge cases and error scenarios
  - Implement security tests for unauthorized access attempts
  - Test backward compatibility with existing functionality
  - Test all updated views with different user roles and permissions
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5_