# treacherytoken.py
# A redbot 3.5 cog that parses information from wowtokenprices.com and returns the price of a wow token.

import discord
from redbot.core import commands
import requests
from bs4 import BeautifulSoup
import time # Added for the try-except block
from urllib3.util.retry import Retry # Added for the retry class
from requests.adapters import HTTPAdapter # Added for the HTTPAdapter

class TreacheryToken(commands.Cog):
    """A cog that shows the current price of a wow token."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the current price of a wow token in US dollars."""
        # Send a message to the context channel saying "Loading WoW Token Information..."
        loading_message = await ctx.send("Loading WoW Token Information...")
        # Create a Session object and mount the adapter with the retry object
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504], allowed_methods=["GET"])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        # Use a try-except block to catch the exception and retry the request after a delay
        try:
            # Get the HTML content from wowtokenprices.com using the session object
            response = session.get("https://wowtokenprices.com/")
        except requests.exceptions.ConnectionError as e:
            print("Connection error: {}".format(e))
            print("Retrying after 5 seconds...")
            time.sleep(5)
            # Recursively retry the request
            return await self.wowtoken(ctx)
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the span element with id="us-money-text" and get its text
        price = soup.find("span", id="us-money-text").text
        # Remove the comma and the dollar sign from the price and convert it to an integer
        price = int(price.replace(",", "").replace("$", ""))
        # Format the price with commas
        price = "{:,}".format(price)
        # Find the p element with id="us-datetime" and get its text
        last_change = soup.find("p", id="us-datetime").text
        # Create an embed with the price and a gold coin emoji
        embed = discord.Embed(title=":coin: WoW Token Price :coin:", color=0xffd700)
        embed.add_field(name="US Region", value=price)
        # Set the footer with the last change time
        embed.set_footer(text=last_change) # Removed the icon_url argument
        # Edit the loading message with the embed
        await loading_message.edit(content=None, embed=embed)
