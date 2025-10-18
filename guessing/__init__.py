from .guessing import GuessOutcome


async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(GuessOutcome(bot))
