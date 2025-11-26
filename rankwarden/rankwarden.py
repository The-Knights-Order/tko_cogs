import discord
from redbot.core import commands, Config
from typing import Optional

class RankWarden(commands.Cog):
    """
    RankWarden: Store and manage user ranks/activity levels manually or by one-time import.
    """

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=12839201923)

        default_member = {
            "rank": None,
            "activity": None,
        }
        self.config.register_member(**default_member)

    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setrank(self, ctx, member: discord.Member, rank: str):
        """Manually set a user's rank."""
        await self.config.member(member).rank.set(rank)
        await ctx.send(f"Stored **{rank}** as the rank for {member.display_name}.")

    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setactivity(self, ctx, member: discord.Member, activity: str):
        """Manually set a user's activity level."""
        await self.config.member(member).activity.set(activity)
        await ctx.send(f"Stored activity level **{activity}** for {member.display_name}.")

    @commands.command()
    async def getrank(self, ctx, member: Optional[discord.Member] = None):
        """Retrieve a user's stored rank and activity."""
        member = member or ctx.author
        data = await self.config.member(member).all()

        rank = data.get("rank", "None")
        activity = data.get("activity", "None")

        await ctx.send(f"**{member.display_name}**\nRank: **{rank}**\nActivity: **{activity}**")

    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def importroles(self, ctx):
        """
        One‑time bulk import: store each member's highest role as their rank.
        """
        count = 0
        for member in ctx.guild.members:
            if len(member.roles) > 1:
                # Highest role is last (except @everyone)
                highest_role = member.roles[-1].name
                await self.config.member(member).rank.set(highest_role)
                count += 1

        await ctx.send(f"Imported ranks for **{count}** members based on their highest role.")

async def setup(bot):
    await bot.add_cog(RankWarden(bot))
