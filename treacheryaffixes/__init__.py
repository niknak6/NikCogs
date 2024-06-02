# Import the cog class
from .treacheryaffixes import TreacheryAffixes

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(TreacheryAffixes(bot))
