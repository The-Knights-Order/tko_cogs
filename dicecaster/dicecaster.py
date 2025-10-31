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
