from redbot.core import commands
import asyncio
import pytgpt.gpt4free as gpt4free

# Ensure the standard asyncio event loop is used
asyncio.set_event_loop(asyncio.new_event_loop())

class BetaAlpha(commands.Cog):
    """A simple cog named BetaAlpha with a testgpt command."""

    def __init__(self, bot):
        self.bot = bot
        self.gpt_bot = gpt4free.GPT4FREE(provider="Koala")

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the GPT4FREE model."""
        response = self.gpt_bot.chat(prompt, stream=False)
        await ctx.send(response)

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
