from redbot.core import commands
from meta_ai_api import MetaAI

class Copilot(commands.Cog):
    """A simple cog to interact with MetaAI API."""

    def __init__(self, bot):
        self.bot = bot
        self.ai = MetaAI()  # Assuming MetaAI can be initialized like this.

    @commands.command()
    async def meta(self, ctx, *, query: str):
        """Fetches response from MetaAI API based on the query."""
        try:
            response = self.ai.prompt(message=query)
            # Assuming the response is a dictionary with a 'message' key.
            await ctx.send(response['message'])
        except Exception as e:
            await ctx.send(f"Error: {str(e)}")

def setup(bot):
    bot.add_cog(Copilot(bot))
