# Import the cog class
from .copilot import Copilot

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(Copilot(bot))
