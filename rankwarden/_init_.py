from .rankwarden import RankWarden

async def setup(bot):
    await bot.add_cog(RankWarden(bot))