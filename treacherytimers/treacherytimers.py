import requests
from bs4 import BeautifulSoup
import discord
import textwrap
from redbot.core import commands

class TreacheryTimers(commands.Cog):
    """A cog that downloads and parses a web page"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timers(self, ctx):
        """Downloads and parses the web page https://www.wowhead.com/classic"""

        # Define the URL to download
        url = "https://www.wowhead.com/classic"

        # Send a GET request to the URL and store the response
        response = requests.get(url)

        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            # Parse the response content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Print the title of the web page
            print(soup.title.string)

            # You can also access other elements of the web page using soup
            # For example, to get all the links in the web page, you can do this:
            links = soup.find_all("a")
            for link in links:
                print(link["href"])

            # Create an embed object
            embed = discord.Embed(title="Web page source", description="The source of the web page you requested")

            # Add the source as a field
            embed.add_field(name="Source", value=response.content)

            # Send the embed to the channel
            await ctx.send(embed=embed)
        else:
            # Handle the error if the response status code is not 200
            print(f"Error: {response.status_code}")

            # Split the source into chunks of 2000 characters each
            chunks = textwrap.wrap(response.content, 2000)

            # Send each chunk as a code block to the channel
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")