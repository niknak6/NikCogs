# Import the cog class
from .treacherypokemonv2 import TreacheryPokemonV2

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(TreacheryPokemonV2(bot))
