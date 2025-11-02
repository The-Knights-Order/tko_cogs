import random
import discord
from redbot.core import commands, app_commands


class DiceCaster(commands.Cog):
    def __init__(self, bot):
        """Initialize the cog and register config defaults."""
        self.bot = bot

    @app_commands.command()
    @app_commands.guild_only()
    async def roll(self, interaction: discord.Interaction, query: str = None):
        """
        Roll any combination of any number of dice, defaults to a single D20.
        Users can type nothing, a single die, or many space-separated dice:
          /roll
          /roll 1D20
          /roll 2D6 3D4
        This cog is heavily inspired by DiceMaiden. The same logic can be found here: https://github.com/Humblemonk/DiceMaiden
        """
        if query == None:
            # Roll a D20 and output the result.
            return

        # Seperate the input into sperate tokens, ie 1D20.
        tokens = str.split(' ')  # Can be one single token.

        # Iterate over the tokens.
        # Validate the token.
        # Roll for the token.
        # Store the value outside the loop.

        # Format and output the rolls.
