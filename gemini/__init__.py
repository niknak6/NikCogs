# Import the cog class
from .gemini import Gemini

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(Gemini(bot))
