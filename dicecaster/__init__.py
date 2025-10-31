from .dicecaster import DiceCaster


async def setup(bot):
    """Setup function for loading the cog."""
    await bot.add_cog(DiceCaster(bot))