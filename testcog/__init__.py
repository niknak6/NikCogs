# Import the cog class
from .testcog import TestCog

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(TestCog(bot))
