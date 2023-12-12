# Import the cog class
from .treacherytimers import TreacheryTimers

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(TreacheryTimers(bot))
