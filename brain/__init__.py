# Import the cog class
from .brain import Brain

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(Brain(bot))
