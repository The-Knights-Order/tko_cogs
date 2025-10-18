import asyncio
from redbot.core import commands, Config


class GuessOutcome(commands.Cog):
    def __init__(self, bot):
        """Initialize the cog and register config defaults."""
        self.bot = bot
        # Use force_registration for safety and a unique identifier
        self.config = Config.get_conf(
            self, identifier=123456789, force_registration=True)
        self.config.register_guild(active_game=None, guesses={})

    @commands.guild_only()
    @commands.command()
    async def startguess(self, ctx, question: str):
        active = await self.config.guild(ctx.guild).active_game()
        if active:
            return await ctx.send("There's already an active guessing round.")
        await self.config.guild(ctx.guild).active_game.set(question)
        await self.config.guild(ctx.guild).guesses.set({})
        await ctx.send(f"Guess the Outcome:\n{question}\nUse !guess <your answer> to play. Results in 24 hours.")
        # fails if the bot is restarted. Using time stamps, shorter sleeps, and a resume timer function would be better.
        await asyncio.sleep(86400)
        await ctx.send("Time's up! Use !reveal <correct answer> to announce the results.")

    @commands.guild_only()
    @commands.command()
    async def guess(self, ctx, user_guess: str):
        active = await self.config.guild(ctx.guild).active_game()
        if not active:
            return await ctx.send("No active guessing game right now.")
        guesses = await self.config.guild(ctx.guild).guesses()
        # Previous guesses are overridden without the user being told.
        guesses[str(ctx.author.id)] = user_guess
        await self.config.guild(ctx.guild).guesses.set(guesses)
        await ctx.send(f"Your guess '{user_guess}' has been recorded, {ctx.author.display_name}.")

    @commands.guild_only()
    @commands.command()
    async def reveal(self, ctx, *, correct_answer: str):
        active = await self.config.guild(ctx.guild).active_game()
        if not active:
            return await ctx.send("No active game to reveal.")
        guesses = await self.config.guild(ctx.guild).guesses()
        if not guesses:
            await ctx.send("No guesses were made.")
            await self.config.guild(ctx.guild).active_game.clear()
            return
        closest_user = None
        closest_diff = float("inf")
        try:
            correct_num = float(correct_answer)
            for uid, guess in guesses.items():
                try:
                    diff = abs(correct_num - float(guess))
                    if diff < closest_diff:
                        closest_diff = diff
                        closest_user = uid
                except ValueError:
                    pass
            if closest_user:  # Always True?
                winner = ctx.guild.get_member(int(closest_user))
                await ctx.send(f"The correct answer was {correct_answer}. Closest guess: {winner.display_name} (off by {closest_diff}).")
            else:
                await ctx.send(f"The correct answer was {correct_answer}. No numeric guesses to compare.")
        except ValueError:
            text = f"The correct answer was {correct_answer}.\n\nGuesses:\n"
            for uid, guess in guesses.items():
                member = ctx.guild.get_member(int(uid))
                text += f"- {member.display_name}: {guess}\n"
            await ctx.send(text)
        await self.config.guild(ctx.guild).active_game.clear()
        await self.config.guild(ctx.guild).guesses.clear()
