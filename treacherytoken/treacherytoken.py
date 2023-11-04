# Import the necessary modules
import discord
from redbot.core import commands
import requests

# Define the cog class
class TreacheryToken(commands.Cog):
    """A cog that shows the WoW token price"""

    def __init__(self, bot):
        self.bot = bot

    # Define the command
    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the WoW token price in US region"""

        # Get the json data from the website
        url = "https://wowtokenprices.com/current_prices.json"
        response = requests.get(url)
        data = response.json()

        # Extract the relevant information
        price = data["us"]["current_price"]
        time = data["us"]["time_of_last_change_unix_epoch"]

        # Format the price with commas
        price = f"{price:,}"

        # Create the dynamic timestamp syntax
        timestamp = f"<t:{time}:f>"

        # Create the embed message
        embed = discord.Embed(title=":coin: WoW Token Price :coin:", color=0x00ff00)
        embed.add_field(name="Current Price", value=f"{price} gold")
        embed.add_field(name="Last Change", value=timestamp) # This is the change I made to move the dynamic timestamp from the embed footer to another field in the embed
        embed.set_footer(text=f"The Last Change time is in your local time.")

        # Send the embed message
        await ctx.send(embed=embed)
