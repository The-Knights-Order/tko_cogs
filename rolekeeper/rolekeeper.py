import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
from typing import List, Tuple
import logging

log = logging.getLogger("red.rolekeeper")


class RoleKeeper(commands.Cog):
    """
    A cog that maintains group-based role hierarchies using slash commands.

    When a user is given a role within a group, they receive the group role (not all lower roles).
    """

    # Define a slash command group for all RoleKeeper commands.
    # This creates the '/rolekeeper' root command.
    rolekeeper_group = discord.app_commands.Group(
        name="rolekeeper",
        description="Manage group-based role hierarchies for your server.",
        # Set default permissions required to see/use the command group in a server's integration settings.
        default_permissions=discord.Permissions(manage_roles=True),
        # Ensure commands are only usable in guilds (servers).
        guild_only=True
    )

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {"groups": {}}
        self.config.register_guild(**default_guild)

    # This method is called when the cog is loaded.
    async def cog_load(self):
        """Adds the slash command group to the bot's command tree upon cog load."""
        self.bot.tree.add_command(self.rolekeeper_group)

    # This method is called when the cog is unloaded.
    def cog_unload(self):
        """Removes the slash command group to allow for clean reloads."""
        self.bot.tree.remove_command(self.rolekeeper_group.name)

    def _parse_roles_from_string(self, guild: discord.Guild, roles_str: str) -> Tuple[List[discord.Role], List[str]]:
        """
        Parses a comma-separated string of role names or IDs into discord.Role objects.
        Returns a tuple of (found_roles, unfound_role_names).
        """
        found_roles = []
        unfound_role_names = []
        role_identifiers = [r.strip() for r in roles_str.split(',') if r.strip()]

        for identifier in role_identifiers:
            role = None
            if identifier.isdigit():
                role = guild.get_role(int(identifier))
            
            if not role and identifier.startswith("<@&") and identifier.endswith(">"):
                try:
                    role_id = int(identifier[3:-1])
                    role = guild.get_role(role_id)
                except (ValueError, TypeError):
                    pass

            if not role:
                role = discord.utils.get(guild.roles, name=identifier)
            if not role:
                role = discord.utils.find(lambda r: r.name.lower() == identifier.lower(), guild.roles)

            if role:
                found_roles.append(role)
            else:
                unfound_role_names.append(identifier)
        
        return found_roles, unfound_role_names

    @rolekeeper_group.command(name="create")
    @discord.app_commands.describe(
        group_name="The unique name for the new role group.",
        group_role="The main role that represents this group (e.g., 'Knight').",
        member_roles_str="Comma-separated list of member role names or IDs (e.g., 'Squire, Page')."
    )
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def rolekeeper_create(self, interaction: discord.Interaction, group_name: str, group_role: discord.Role, member_roles_str: str):
        """Create a new group, specifying its group role and member roles."""
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        member_roles, unfound_roles = self._parse_roles_from_string(guild, member_roles_str)

        if not member_roles:
            await interaction.followup.send("You must specify at least one valid member role.")
            return
        
        if unfound_roles:
            await interaction.followup.send(
                f"Could not find some specified member roles: `{', '.join(unfound_roles)}`. "
                "Please ensure names are exact or use IDs."
            )
            return

        bot_member = guild.get_member(self.bot.user.id)
        all_roles_to_manage = [group_role] + member_roles
        unmanageable_roles = [role.name for role in all_roles_to_manage if role >= bot_member.top_role]
        
        if unmanageable_roles:
            await interaction.followup.send(
                f"I cannot manage these roles (they are above my highest role): {', '.join(unmanageable_roles)}"
            )
            return

        async with self.config.guild(guild).groups() as groups:
            if group_name in groups:
                await interaction.followup.send(
                    f"Group '{group_name}' already exists. Use `/rolekeeper delete` first or choose a different name."
                )
                return
            groups[group_name] = {
                "group_role": group_role.id,
                "member_roles": [role.id for role in member_roles]
            }

        role_names = [role.name for role in member_roles]
        await interaction.followup.send(
            f"Group '{group_name}' created with group role: **{group_role.name}** "
            f"and member roles: **{' -> '.join(role_names)}**",
            ephemeral=False
        )

    @rolekeeper_group.command(name="delete")
    @discord.app_commands.describe(group_name="The name of the group to delete.")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def rolekeeper_delete(self, interaction: discord.Interaction, group_name: str):
        """Delete an existing role group by its name."""
        async with self.config.guild(interaction.guild).groups() as groups:
            if group_name in groups:
                del groups[group_name]
                await interaction.response.send_message(f"Group '{group_name}' deleted.")
            else:
                await interaction.response.send_message(f"Group '{group_name}' not found.", ephemeral=True)

    @rolekeeper_group.command(name="addrole")
    @discord.app_commands.describe(
        group_name="The name of the group to modify.",
        role="The member role to add to the group."
    )
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def rolekeeper_addrole(self, interaction: discord.Interaction, group_name: str, role: discord.Role):
        """Add a new member role to an existing group."""
        async with self.config.guild(interaction.guild).groups() as groups:
            if group_name not in groups:
                await interaction.response.send_message(f"Group '{group_name}' not found.", ephemeral=True)
                return
            if role.id in groups[group_name]["member_roles"]:
                await interaction.response.send_message(f"Role '{role.name}' is already in group '{group_name}'.", ephemeral=True)
                return
            groups[group_name]["member_roles"].append(role.id)
            await interaction.response.send_message(f"Role '{role.name}' added to group '{group_name}'.")

    @rolekeeper_group.command(name="removerole")
    @discord.app_commands.describe(
        group_name="The name of the group to modify.",
        role="The member role to remove from the group."
    )
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def rolekeeper_removerole(self, interaction: discord.Interaction, group_name: str, role: discord.Role):
        """Remove a member role from an existing group."""
        async with self.config.guild(interaction.guild).groups() as groups:
            if group_name not in groups:
                await interaction.response.send_message(f"Group '{group_name}' not found.", ephemeral=True)
                return
            if role.id not in groups[group_name]["member_roles"]:
                await interaction.response.send_message(f"Role '{role.name}' is not in group '{group_name}'.", ephemeral=True)
                return
            groups[group_name]["member_roles"].remove(role.id)
            await interaction.response.send_message(f"Role '{role.name}' removed from group '{group_name}'.")

    @rolekeeper_group.command(name="list")
    @discord.app_commands.checks.has_permissions(manage_roles=True)
    async def rolekeeper_list(self, interaction: discord.Interaction):
        """List all role groups configured for this server."""
        guild = interaction.guild
        groups = await self.config.guild(guild).groups()
        
        if not groups:
            await interaction.response.send_message("No groups configured for this server.", ephemeral=True)
            return

        embed = discord.Embed(title="RoleKeeper Groups", color=await self.bot.get_embed_color(interaction))
        for group_name, data in groups.items():
            group_role = guild.get_role(data["group_role"])
            member_roles = [guild.get_role(rid) for rid in data.get("member_roles", [])]
            
            group_role_name = group_role.name if group_role else f"❌ Deleted Role (ID: {data['group_role']})"
            
            member_role_names = []
            for role_obj, role_id in zip(member_roles, data.get("member_roles", [])):
                member_role_names.append(role_obj.name if role_obj else f"❌ Deleted Role (ID: {role_id})")
            
            value_str = f"**Group Role:** {group_role_name}\n**Member Roles:** {' -> '.join(member_role_names) or 'None'}"
            
            embed.add_field(
                name=f"▶ {group_name}",
                value=value_str,
                inline=False
            )
        await interaction.response.send_message(embed=embed)