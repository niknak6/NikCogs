# Import the cog class
from .pinfill import PinFill

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(PinFill(bot))
