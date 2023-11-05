from redbot.core import commands
import requests

class TreacheryToken(commands.Cog):
    """A cog that shows the price of the wow token"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the current, 48h low and 48h high price of the wow token in US region"""
        # Get the json data from the url
        url = "https://data.wowtoken.app/token/history/us/48h.json"
        response = requests.get(url)
        data = response.json()

        # Get the current price from the last entry
        current = data[-1]["value"]

        # Get the 48h low and high price by looping through the data
        low = high = current
        for entry in data:
            value = entry["value"]
            if value < low:
                low = value
            if value > high:
                high = value

        # Format the prices with commas and gold icon
        current = f"{current:,} \N{CURRENCY EXCHANGE}"
        low = f"{low:,} \N{CURRENCY EXCHANGE}"
        high = f"{high:,} \N{CURRENCY EXCHANGE}"

        # Send the message with the prices
        await ctx.send(f"The current price of the wow token is {current}.\nThe 48h low price is {low}.\nThe 48h high price is {high}.")
