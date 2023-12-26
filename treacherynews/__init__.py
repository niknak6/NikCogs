# Import the cog class
from .treacherynews import TreacheryNews

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(TreacheryNews(bot))
