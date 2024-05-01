import asyncio
from redbot.core import commands
import pytgpt.gpt4free as gpt4free

class BetaAlpha(commands.Cog):
    """Cog to interact with GPT4Free using Feedough provider."""

    def __init__(self, bot):
        self.bot = bot
        # Ensure the default asyncio event loop is used
        asyncio.set_event_loop(asyncio.new_event_loop())
        self.gpt_bot = gpt4free.GPT4FREE(provider="Feedough")

    @commands.command()
    async def testgpt(self, ctx, *, query: str):
        """Send a query to the GPT model and return the response."""
        try:
            response = self.gpt_bot.chat(query)
            await ctx.send(response)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

# Setup function to add this cog to Redbot
def setup(bot):
    bot.add_cog(BetaAlpha(bot))
