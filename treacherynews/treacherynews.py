# Import the required modules
import discord
from redbot.core import commands
import requests

# Define the cog class
class CurrencyConvert(commands.Cog):
    """Built to help with currency conversions in Treachery Discord"""

    def __init__(self, bot):
        self.bot = bot

    # Define the command
    @commands.command(name="cconv")
    async def cconv(self, ctx, from_currency: str, to_currency: str, amount: float):
        """Converts currency from one to another.

        Example:
        - `[p]cconv USD CAD 100`
        """
        # Validate the input parameters
        if amount <= 0:
            await ctx.send("The amount must be positive.")
            return
        if len(from_currency) != 3 or len(to_currency) != 3:
            await ctx.send("The currency codes must be three letters long.")
            return

        # Convert the currency codes to uppercase
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Make a request to the API
        url = f"https://open.exchangerate-api.com/v6/latest"
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            data = response.json()

            # Check if the conversion rates exist
            if from_currency in data["rates"] and to_currency in data["rates"]:
                # Get the conversion rates relative to USD
                from_rate = data["rates"][from_currency]
                to_rate = data["rates"][to_currency]

                # Calculate the conversion rate between the currencies
                rate = to_rate / from_rate

                # Calculate the converted amount
                converted_amount = round(amount * rate, 2)

                # Format and send the output message
                output = f"{amount} {from_currency} is equal to {converted_amount} {to_currency}."
                await ctx.send(output)
            else:
                # Send an error message
                await ctx.send("The conversion rate for these currencies is not available.")
        else:
            # Send an error message
            await ctx.send("The request to the API failed.")
