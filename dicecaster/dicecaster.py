import random
import discord
import re
from redbot.core import commands, app_commands


class DiceCaster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roll", description="Roll any combination of dice (e.g., 1d20, 2d6 3d4)")
    @app_commands.guild_only()
    async def roll(self, interaction: discord.Interaction, query: str = None):
        """
        Roll any combination of any number of dice, defaults to a single D20.
        Users can type nothing, a single die, or many space-separated dice:
          /roll
          /roll 1D20
          /roll 2D6 3D4
        """
        if query is None:
            # Default roll: 1d20
            result = random.randint(1, 20)
            await interaction.response.send_message(f"🎲 You rolled **1d20** → **{result}**")
            return

        # Split the input into tokens (e.g., ["2d6", "3d4"])
        tokens = query.upper().split()

        total_sum = 0
        results_msg = []

        pattern = re.compile(r'^[1-9]\d{0,1}D[2-9]\d{0,2}$', re.IGNORECASE)

        for token in tokens:
            # Validate token (e.g., "2D6")
            if not pattern.fullmatch(token):
                results_msg.append(
                    f"❌ Invalid format: `{token}` (must be like 2d6)")
                continue

            try:
                num, sides = token.split('D')
                num = int(num) if num else 1
                sides = int(sides) if num else 2

            except ValueError:
                results_msg.append(f"❌ Invalid number in `{token}`")
                continue

            # Roll the dice
            rolls = [random.randint(1, sides) for _ in range(num)]
            subtotal = sum(rolls)
            total_sum += subtotal

            # Add to message
            rolls_display = ", ".join(str(r) for r in rolls)
            results_msg.append(
                f"🎲 `{token}` → {rolls_display} (Total: {subtotal})")

        # Combine and send final message
        msg = "\n".join(results_msg)
        msg += f"\n**Grand Total: {total_sum}**" if len(tokens) > 1 else ""

        await interaction.response.send_message(msg)
