import random
from redbot.core import commands, Config


class DiceCaster(commands.Cog):
    def __init__(self, bot):
        """Initialize the cog and register config defaults."""
        self.bot = bot
        # Use force_registration for safety and a unique identifier
        self.config = Config.get_conf(
            self, identifier=123456789, force_registration=True)
        self.config.register_guild(active_game=None, guesses={})

    @commands.command()
    async def d4(self, ctx):
        """Rolls a 4-sided die."""
        result = random.randint(1, 4)
        await ctx.send(f"🎲 You rolled a **{result}** on a d4!")

    @commands.command()
    async def d6(self, ctx):
        """Rolls a 6-sided die."""
        result = random.randint(1, 6)
        await ctx.send(f"🎲 You rolled a **{result}** on a d6!")

    @commands.command()
    async def d8(self, ctx):
        """Rolls an 8-sided die."""
        result = random.randint(1, 8)
        await ctx.send(f"🎲 You rolled a **{result}** on a d8!")

    @commands.command()
    async def d10(self, ctx):
        """Rolls a 10-sided die."""
        result = random.randint(1, 10)
        await ctx.send(f"🎲 You rolled a **{result}** on a d10!")

    @commands.command()
    async def d12(self, ctx):
        """Rolls a 12-sided die."""
        result = random.randint(1, 12)
        await ctx.send(f"🎲 You rolled a **{result}** on a d12!")

    @commands.command()
    async def d20(self, ctx):
        """Rolls a 20-sided die."""
        result = random.randint(1, 20)
        await ctx.send(f"🎲 You rolled a **{result}** on a d20!")
