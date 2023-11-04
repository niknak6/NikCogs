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
        # Find the p element with id="us-datetime" using its CSS selector and get its text
        time = soup.select_one("p#region-date").text
        # Format the time as you like
        time = f"Last updated at {time}"
        # Create an embed with the price and a gold coin emoji
        embed = discord.Embed(title=":coin: WoW Token Price :coin:", color=0xffd700)
        embed.add_field(name="US Region", value=price)
        # Add another field to the embed with the time and a clock emoji
        embed.add_field(name="Update Time", value=f":clock1: {time}")
        # Edit the loading message with the embed
        await loading_message.edit(content=None, embed=embed)
