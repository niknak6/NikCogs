from redbot.core import commands
import pytgpt.gpt4free as gpt4free
from concurrent.futures import ThreadPoolExecutor

class BetaAlpha(commands.Cog):
    """A simple cog named BetaAlpha with a testgpt command."""

    def __init__(self, bot):
        self.bot = bot
        self.gpt_bot = gpt4free.GPT4FREE(provider="Feedough")

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the GPT4FREE model."""
        # Use a ThreadPoolExecutor to handle the synchronous gpt_bot.chat call
        with ThreadPoolExecutor() as executor:
            response = await self.bot.loop.run_in_executor(executor, self.gpt_bot.chat, prompt)
        await ctx.send(response)

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
