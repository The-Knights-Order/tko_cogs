import random
from redbot.core import commands


class DiceCaster(commands.Cog):
    def __init__(self, bot):
        """Initialize the cog and register config defaults."""
        self.bot = bot
