from redbot.core import commands
import pytgpt.gpt4free as gpt4free

class BetaAlpha(commands.Cog):
    """A simple cog named BetaAlpha with a testgpt command."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the GPT4FREE model, starting a new conversation each time."""
        gpt_bot = gpt4free.GPT4FREE(provider="Feedough", is_conversation=False)
        response = await self.bot.loop.run_in_executor(None, gpt_bot.chat, prompt)
        await ctx.send(response)

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
