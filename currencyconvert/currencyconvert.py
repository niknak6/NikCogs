import discord
from redbot.core import commands
import requests

class CurrencyConvert(commands.Cog):
    """Built to help with currency conversions in Treachery Discord"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="cconv")
    async def cconv(self, ctx, from_currency: str, to_currency: str, amount: float):
        """Converts currency from one to another.

        Example:
        - `[p]cconv USD CAD 100`
        """
        if amount <= 0 or len(from_currency) != 3 or len(to_currency) != 3:
            return await ctx.send("Invalid input. Amount must be positive and currency codes must be 3 letters long.")

        from_currency, to_currency = from_currency.upper(), to_currency.upper()

        response = requests.get(f"https://open.exchangerate-api.com/v6/latest")
        if response.status_code != 200:
            return await ctx.send("The request to the API failed.")

        data = response.json()
        if from_currency not in data["rates"] or to_currency not in data["rates"]:
            return await ctx.send("The conversion rate for these currencies is not available.")

        from_rate, to_rate = data["rates"][from_currency], data["rates"][to_currency]
        converted_amount = round(amount * to_rate / from_rate, 2)

        await ctx.send(f"{amount} {from_currency} is equal to {converted_amount} {to_currency}.")
