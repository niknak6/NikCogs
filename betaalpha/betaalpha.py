from redbot.core import commands
from pytgpt.leo import LEO

class BetaAlpha(commands.Cog):
    """A simple cog named BetaAlpha with a testgpt command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the LEO model."""
        bot = LEO()
        response = bot.chat(prompt)
        await ctx.send(response)

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
