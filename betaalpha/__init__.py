# Import the cog class
from .betaalpha import BetaAlpha

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(BetaAlpha(bot))
