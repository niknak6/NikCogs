# Import the cog class
from .treacherypokemon import TreacheryPokemon

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(TreacheryPokemon(bot))
