"""RoleKeeper Cog - Group-based role management for RedBot."""
import discord
from redbot.core import commands, Config
from redbot.core.bot import Red
import logging

log = logging.getLogger("red.rolekeeper")


class RoleKeeper(commands.Cog):
    """Maintains group-based role hierarchies. When a user is given any member role in a group, they receive the group role."""

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        default_guild = {"groups": {}}
        self.config.register_guild(**default_guild)

    # ==========================================================================
    # Shared helpers
    # ==========================================================================
    
    async def _get_groups_raw(self, guild):
        return await self.config.guild(guild).groups() or {}

    async def _get_groups_normalized(self, guild):
        raw = await self._get_groups_raw(guild)
        return {k.lower(): v for k, v in raw.items()}

    async def _save_groups(self, guild: discord.Guild, data):
        """Save groups back to config (normalizes keys to lowercase)."""
        normalized = {k.lower() if isinstance(k, str) else str(k): v for k, v in data.items()}
        await self.config.guild(guild).groups.set(normalized)

    async def _validate_hierarchy(self, guild: discord.Guild, roles):
        """Check bot hierarchy. Returns unmanageable role names."""
        bot_member = await self.bot.fetch_user(guild.get_member(self.bot.user.id).id) if guild.get_member(self.bot.user.id) else None
        if not bot_member:
            return ["Bot member not found"]
        return [r.name for r in roles if r >= bot_member.top_role]

    async def _format_group_display(self, data, guild):
        """Format group display text."""
        gr = data.get("group_role")
        mr = data.get("member_roles", []) or []
        
        if isinstance(gr, int):
            group_obj = guild.get_role(gr)
        elif isinstance(gr, discord.Role):
            group_obj = gr
        else:
            group_obj = None

        member_objs = []
        for rid in mr:
            r = guild.get_role(rid) if isinstance(rid, int) else (rid if hasattr(rid, 'name') else None)
            member_objs.append(r)

        group_name = group_obj.name if group_obj else f"<Deleted Role: {data['group_role']}>"
        member_names = [o.name if o else f"<Deleted Role: {rid}>" for o, rid in zip(member_objs, mr)]
        return f"Group Role: {group_name}\nMembers: {' -> '.join(member_names)}"

    async def _fix_member_groups(self, member, groups):
        """Add missing group roles. Returns count of fixes."""
        fixes = 0
        guild_id = member.guild.id
        
        for name, data in groups.items():
            gr = data["group_role"]
            mrs = data["member_roles"] or []
            if not gr or not mrs:
                continue

            group_obj = None
            if isinstance(gr, int):
                guild = self.bot.get_guild(guild_id)
                if guild:
                    group_obj = guild.get_role(gr)
            
            found_member = False
            for mr in mrs:
                if not hasattr(mr, 'id'):
                    continue
                mr_obj = self.bot.get_guild(guild_id).get_role(mr.id) if isinstance(mr, int) else (mr if hasattr(mr, 'name') else None)
                if mr_obj and mr_obj in member.roles:
                    found_member = True
                    break

            if found_member and group_obj and group_obj not in member.roles:
                try:
                    await member.add_roles(group_obj, reason="RoleKeeper")
                    fixes += 1
                    log.info(f"Added {group_obj.name} to {member.display_name}")
                except Exception as e:
                    log.warning(f"Fix failed for {member}: {e}")

        return fixes

    # ==========================================================================
    # Commands
    # ==========================================================================

    @commands.group()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def group(self, ctx):
        """Command group for managing role groups."""
        pass

    @group.command(name="add")
    @commands.has_permissions(administrator=True)
    async def group_add(self, ctx, group_name: str, group_role: discord.Role, *member_roles: discord.Role):
        """Add a new group. First role is the group role; rest are member roles."""
        if not member_roles:
            await ctx.send("You must specify at least one member role (after the group role).")
            return

        unmanageable = await self._validate_hierarchy(ctx.guild, [group_role] + list(member_roles))
        if unmanageable:
            await ctx.send(f"I cannot manage these roles (they are above my highest role): {', '.join(unmanageable)}")
            return

        async with self.config.guild(ctx.guild).groups() as groups:
            normalized_key = group_name.lower()
            if normalized_key in groups:
                existing_original = [k for k in groups.keys() if k.lower() == normalized_key][0]
                await ctx.send(f"A group named '{group_name}' (or '{existing_original}') already exists.")
                return
            
            groups[normalized_key] = {
                "group_role": group_role.id,
                "member_roles": [role.id for role in member_roles]
            }

        role_names = [role.name for role in member_roles]
        await ctx.send(f"Group '{group_name}' created with group role: {group_role.name} and member roles: {' -> '.join(role_names)}")

    @group.command(name="remove", aliases=["delete"])
    @commands.has_permissions(administrator=True)
    async def group_remove(self, ctx, group_name: str):
        """Remove a group by name."""
        groups = await self._get_groups_normalized(ctx.guild)
        normalized_key = group_name.lower()

        if normalized_key in groups:
            del groups[normalized_key]
            await self._save_groups(ctx.guild, groups)
            await ctx.send(f"Group '{group_name}' removed.")
        else:
            await ctx.send(f"No group named '{group_name}' found (case-insensitive).")

    @group.command(name="list", aliases=["ls"])
    @commands.has_permissions(administrator=True)
    async def group_list(self, ctx):
        """List all groups for this server."""
        groups = await self._get_groups_normalized(ctx.guild)

        if not groups:
            await ctx.send("No groups configured for this server.")
            return

        embeds = []
        chunk_size = 25
        items_per_chunk = len(groups) // chunk_size + 1
        
        for i in range(items_per_chunk):
            start = i * chunk_size
            end = min(start + chunk_size, len(groups))
            chunk = list(groups.items())[start:end]

            embed = discord.Embed(title="Role Groups", color=discord.Color.blue())
            
            for group_name, data in chunk:
                display_text = await self._format_group_display(data, ctx.guild)
                if len(embed.description or "") + len(display_text.replace('\n', ' ')) > 2048:
                    break
                embed.add_field(name=group_name, value=display_text, inline=False)

            if i < items_per_chunk - 1:
                embed.footer.text = f"Page {i+1} of {items_per_chunk}"
            
            await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def groupcheck(self, ctx, member: discord.Member):
        """Check a specific member's role status against all groups."""
        groups = await self._get_groups_normalized(ctx.guild)

        if not groups:
            await ctx.send("No groups configured for this server.")
            return

        missing = []
        
        for group_name, data in groups.items():
            gr = data["group_role"]
            mrs = data["member_roles"] or []
            if not gr or not mrs:
                continue

            found_member = any(
                hasattr(mr, 'id') and mr.id is not None 
                for mr in [self.bot.get_guild(member.guild.id).get_role(mr.id) if isinstance(mr, int) else (mr if hasattr(mr, 'name') else None) for mr in mrs]
            )

            group_obj = self.bot.get_guild(member.guild.id).get_role(gr) if isinstance(gr, int) else (gr if hasattr(gr, 'name') else None)
            
            has_member_role = found_member and group_obj and group_obj in member.roles
            
            if not has_member_role:
                missing.append(f"**{group_name}**: Has member roles but missing group role.")

        embed = discord.Embed(title=f"Role Check for {member.display_name}", color=discord.Color.green())
        
        if missing:
            await ctx.send("No groups configured.", mention_author=False)
            return
        
        if not groups:
            await ctx.send("No groups found.", mention_author=False)
            return

        embed.add_field(name="Status", value="All group roles are correctly assigned." if not missing else "Some users need fixes.", inline=False)
        
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def fix(self, ctx, member: discord.Member = None):
        """Fix missing group roles for a user. Omit user to fix all."""
        if not member:
            members_to_fix = [m for m in await ctx.guild.members() if m.bot is False]
            total_fixed = 0
            
            # Process in batches
            batch_size = 50
            for i in range(0, len(members_to_fix), batch_size):
                batch = members_to_fix[i:i + batch_size]
                fixes_in_batch = sum(await self._fix_member_groups(m, await self._get_groups_normalized(ctx.guild)) for m in batch)
                total_fixed += fixes_in_batch

            embed = discord.Embed(title="Batch Fix Complete", color=discord.Color.green())
            embed.add_field(name="Total Users Fixed", value=str(total_fixed), inline=True)
            await ctx.send(embed=embed)
        else:
            groups = await self._get_groups_normalized(ctx.guild)
            added = await self._fix_member_groups(member, groups)

            if added > 0:
                embed = discord.Embed(title=f"Fixed for {member.display_name}", color=discord.Color.green())
                embed.add_field(name="Added", value=f"**{added}** group role(s)", inline=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No fixes needed for {member.display_name}.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def addtogroup(self, ctx, group_name: str, role: discord.Role):
        """Add a role to an existing group's member roles."""
        groups = await self._get_groups_normalized(ctx.guild)
        normalized_key = group_name.lower()

        if normalized_key not in groups:
            await ctx.send(f"Group '{group_name}' not found.")
            return

        rid = role.id if hasattr(role, 'id') else role
        member_roles = groups[normalized_key].get("member_roles", []) or []

        if rid in member_roles:
            await ctx.send(f"Role '{role.name}' is already in group '{group_name}'.")
            return

        member_roles.append(rid)
        groups[normalized_key]["member_roles"] = member_roles
        await self._save_groups(ctx.guild, groups)
        
        await ctx.send(f"Role '{role.name}' added to group '{group_name}'.")

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def listgroups(self, ctx):
        """List all groups and their roles."""
        await self.group_list(ctx)

    # ==========================================================================
    # Listeners: Automatic enforcement
    # ==========================================================================

    @commands.event
    async def on_member_add(self, member: discord.Member):
        """Ensure new members have correct group roles."""
        groups = await self._get_groups_normalized(member.guild)
        if not groups:
            return
        await self._fix_member_groups(member, groups)

    @commands.event
    async def on_role_add(self, member: discord.Member, role: discord.Role):
        """Check if a newly granted role triggers group role requirements."""
        guild = member.guild.id
        
        for gid in [member.guild.id]:
            try:
                groups = await self._get_groups_normalized(member.guild)
                
                for name, data in groups.items():
                    gr = data["group_role"]
                    mrs = data["member_roles"] or []

                    if not gr or not mrs:
                        continue

                    # Check if newly granted role is a member role
                    new_role_id = role.id
                    
                    found_member = False
                    for mr in mrs:
                        if hasattr(mr, 'id') and mr.id == new_role_id:
                            found_member = True
                            break

                    if found_member:
                        group_obj = self.bot.get_guild(gid).get_role(gr)
                        if group_obj and group_obj not in member.roles:
                            try:
                                await member.add_roles(group_obj, reason="RoleKeeper: Auto enforcement")
                                log.info(f"Auto-added {group_obj.name} to {member.display_name}")
                            except Exception as e:
                                log.warning(f"Auto-add failed for {member}: {e}")
            except Exception as e:
                log.error(f"on_role_add error: {e}")

    @commands.event
    async def on_guild_remove(self, guild):
        """Clear guild config when bot leaves."""
        try:
            await self.config.guild(guild).groups.set({})
        except Exception as e:
            log.error(f"Failed to clear guild config for {guild.name}: {e}")

    # ==========================================================================
    # Error handling
    # ==========================================================================

    async def cog_command_error(self, ctx, error):
        """Handle cog-specific errors."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have permission to use this command.")
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send("I don't have the necessary permissions to perform this action.")
        elif isinstance(error, commands.CommandNotFound):
            log.debug(f"Command not found: {error}")
        else:
            log.exception("Unexpected error", exc_info=error)
