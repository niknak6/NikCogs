# Import the necessary modules
import discord
from discord.ext import commands
import requests

# Define the cog class
class TreacheryToken(commands.Cog):
    """A cog that parses WoW token information from a JSON source."""

    def __init__(self, bot):
        self.bot = bot

    # Define the command
    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the current price and time of last change of the WoW token in US region."""

        # Get the JSON data from the source
        url = "https://wowtokenprices.com/current_prices.json"
        response = requests.get(url)
        data = response.json()

        # Extract the relevant data
        price = data["us"]["current_price"]
        time = data["us"]["time_of_last_change_utc_timezone"]

        # Format the price with commas
        price = f"{price:,}"

        # Create an embed message
        embed = discord.Embed(title=":coin: WoW Token Price :coin:", color=0x00ff00)
        embed.add_field(name="Current Price", value=f"{price} gold")
        embed.set_footer(text=f"Last updated: {time}")

        # Send the embed message
        await ctx.send(embed=embed)

# Add the cog to the bot
def setup(bot):
    bot.add_cog(TreacheryToken(bot))
