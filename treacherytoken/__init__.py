# Import the cog class
from .treacherytoken import TreacheryToken

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(TreacheryToken(bot))
