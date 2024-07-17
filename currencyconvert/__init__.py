# Import the cog class
from .currencyconvert import CurrencyConvert

# Define the setup function
async def setup(bot):
    # Add the cog to the bot
    await bot.add_cog(CurrencyConvert(bot))
