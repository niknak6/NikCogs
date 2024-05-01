from redbot.core import commands
import pytgpt.gpt4free as gpt4free
import asyncio
import threading

class BetaAlpha(commands.Cog):
    """A simple cog named BetaAlpha with a testgpt command."""

    def __init__(self, bot):
        self.bot = bot
        self.gpt_bot = gpt4free.GPT4FREE(provider="Koala")

    def run_in_thread(self, func, *args):
        """Helper function to run a function in a separate thread."""
        result = []
        def wrapper():
            result.append(func(*args))
        thread = threading.Thread(target=wrapper)
        thread.start()
        thread.join()
        return result[0]

    @commands.command()
    async def testgpt(self, ctx, *, prompt: str):
        """Responds with output from the GPT4FREE model."""
        # Run the chat function in a separate thread to avoid event loop issues
        response = await self.bot.loop.run_in_executor(None, self.run_in_thread, self.gpt_bot.chat, prompt, False)
        await ctx.send(response)

def setup(bot):
    bot.add_cog(BetaAlpha(bot))
