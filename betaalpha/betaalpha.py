from redbot.core import commands
import pytgpt.gpt4free as gpt4free  # Importing the gpt4free module from pytgpt

class BetaAlpha(commands.Cog):
    """
    BetaAlpha Cog for querying the Feedough provider using the pytgpt library.
    """

    def __init__(self, bot):
        self.bot = bot
        self.bot_gpt = gpt4free.GPT4FREE(provider="Feedough")  # Initialize the GPT4FREE with Feedough provider

    @commands.command()
    async def testgpt(self, ctx, *, query: str):
        """
        Handles the !testgpt command with a user query.
        Usage: !testgpt <your query here>
        """
        try:
            response = self.bot_gpt.chat(query)  # Send query to Feedough provider
            await ctx.send(f"Feedough Response: {response}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")  # Handle exceptions gracefully

def setup(bot):
    """
    Setup function to add this cog to Redbot.
    """
    bot.add_cog(BetaAlpha(bot))
