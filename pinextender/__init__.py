# Import the cog class
from .pinextender import PinExtender

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(PinExtender(bot))
