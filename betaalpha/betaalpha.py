from redbot.core import commands
import pytgpt.feedough as feedough  # Importing the Feedough module from pytgpt

class BetaAlpha(commands.Cog):
    """
    BetaAlpha Cog for querying the Feedough provider using the pytgpt library.
    """

    def __init__(self, bot):
        self.bot = bot
        self.bot_feedough = feedough.Feedough()  # Initialize the Feedough provider

    @commands.command()
    async def testgpt(self, ctx, *, query: str):
        """
        Handles the !testgpt command with a user query.
        Usage: !testgpt <your query here>
        """
        try:
            response = self.bot_feedough.chat(query)  # Send query to Feedough provider
            await ctx.send(f"Feedough Response: {response}")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")  # Handle exceptions gracefully

def setup(bot):
    """
    Setup function to add this cog to Redbot.
    """
    bot.add_cog(BetaAlpha(bot))
