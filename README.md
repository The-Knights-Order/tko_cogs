# TKO-Rolekeeper

A RedBot cog for the TKO Rolekeeper Discord bot.

## Features

- **Group Role Management**: Define groups, each with a group role and a list of member roles. When a user is given any member role in a group, the bot ensures they also have the group role (but does not add or remove other roles).
- **Automatic Group Role Enforcement**: Listens for role updates and ensures users with a member role in a group always have the group role.
- **Audit Command**: Sweep through all server members to check and fix missing group roles according to configured groups.
- **Admin-Only Commands**: All commands require administrator permissions.
- **Permission Checks**: Ensures the bot has proper permissions before attempting role modifications.
- **Case-Insensitive Group Names**: `Council` and `council` refer to the same group (stored in lowercase for collision prevention).

## Installation

1. Add this repository to your Red Bot instance:
    ```
    [p]repo add tko-rolekeeper <repo_url>
    ```
    Replace `<repo_url>` with the actual URL of this repository.
2. Install the cog:
    ```
    [p]cog install tko-rolekeeper rolekeeper
    ```
3. Load the cog:
    ```
    [p]load rolekeeper
    ```

## Commands

All commands require administrator permissions.

### Group Management

- `[p]group add <group_name> <group_role> <member_role1> <member_role2> ...` - Create a new group (first role is the group role, rest are member roles). **Rejects duplicate names** (case-insensitive).
- `[p]group remove <group_name>` / `[p]group delete <group_name>` - Remove a group by name.
- `[p]group list` / `[p]group ls` - List all configured groups and their roles. Supports >25 groups via chunked embeds.

### Member Management

- `[p]groupcheck <member>` - Check a specific member's role status against all groups (shows what group roles they have or are missing).
- `[p]fix [<member>]` - Fix missing group roles for one user or all users in the guild. Uses batching to avoid rate limits.

### Group Editing

- `[p]addtogroup <group_name> <role>` - Add a role to an existing group's member roles (appends if not duplicate).

### Auditing / Reporting

- `[p]listgroups` - List all groups and their roles (alias for `group list`).
- **Note**: The cog now uses case-insensitive lookups internally. Group names are stored in lowercase to prevent duplicates like "Council" and "council".

## Example Usage

```
[p]group add Council CouncilRole Advisor Officer
[p]addtogroup Council SeniorAdvisor
[p]fix @user
```

This creates a group called "Council" with "CouncilRole" as the group role and "Advisor", "Officer", and "SeniorAdvisor" as member roles. If a user is given any of the member roles (e.g., "Advisor"), the bot ensures they also have the "CouncilRole".

## Behavior Notes

- **Flat Enforcement**: Any single member role grants the group role — there is no ordering or cascade logic. Member roles are unordered; granting one does not imply anything about others.
- **Never Removes Roles**: The cog only adds missing group roles. It never removes any other roles (member roles, group roles assigned by external means).
- **Orphaned Group Roles**: If you delete a group using `[p]group remove`, the existing group role remains assigned to members but is no longer managed. This is intentional — the cog will not remove roles.

## Permissions

- All commands require Administrator permissions
- Bot needs `Manage Roles` permission and must be higher in role hierarchy than all managed roles (the bot checks this before saving)
