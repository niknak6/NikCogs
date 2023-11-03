# treacherytoken.py
# A redbot 3.5 cog that parses information from wowtokenprices.com and returns the price of a wow token.

import discord
from redbot.core import commands
import requests
from bs4 import BeautifulSoup

class TreacheryToken(commands.Cog):
    """A cog that shows the current price of a wow token."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the current price of a wow token in US dollars."""
        # Send a message to the context channel saying "Loading WoW Token Information..."
        loading_message = await ctx.send("Loading WoW Token Information...")
        # Get the HTML content from wowtokenprices.com
        response = requests.get("https://wowtokenprices.com/")
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the span element with id="us-money-text" and get its text
        price = soup.find("span", id="us-money-text").text
        # Remove the comma and the dollar sign from the price and convert it to an integer
        price = int(price.replace(",", "").replace("$", ""))
        # Format the price with commas
        price = "{:,}".format(price)
        # Create an embed with the price and a gold coin emoji
        embed = discord.Embed(title=":coin: WoW Token Price :coin:", color=0xffd700)
        embed.add_field(name="US Region", value=price)
        # Edit the loading message with the embed
        await loading_message.edit(content=None, embed=embed)
