import requests
import discord
import textwrap
import json
import re
from datetime import datetime
import pytz
from redbot.core import commands, checks

class TreacheryTimers(commands.Cog):
    """A cog that downloads and parses a web page"""

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890)  # Use a unique identifier
        default_guild = {
            "raids": []
        }
        self.config.register_guild(**default_guild)

    def get_web_data(self):
        """Get the data from the web page"""
        # Define the URL to download
        url = "https://www.wowhead.com/classic"

        # Send a GET request to the URL and store the response
        response = requests.get(url)

        # Get the response content as a string
        web_page_source = response.text

        # Define a regex pattern to match the lines with the ending, endingShort, endingUt, and name fields in the source
        pattern = r"\{\"ending\":\".+?\",\"endingShort\":\".+?\",\"endingUt\":\d+,\"name\":\".+?\",.+?\}"

        # Find all the matches of the pattern in the web page source
        matches = re.findall(pattern, web_page_source)

        # Convert the matches to Python objects
        data = [json.loads(match) for match in matches]

        return data

    def get_raids(self):
        """Get the available raids"""
        data = self.get_web_data()

        # Extract the raid names
        raids = [item["name"] for item in data]

        return raids

    @commands.group()
    async def timers(self, ctx):
        """Commands related to raid timers"""
        pass

    @timers.command()
    @checks.admin_or_permissions(manage_guild=True)
    async def settings(self, ctx):
        """Set the server's raid preferences"""
        # Get the available raids
        raids = self.get_raids()
        raid_dict = {i+1: raid for i, raid in enumerate(raids)}

        # Send the available raids to the user
        await ctx.send("\n".join([f"{i} - {raid}" for i, raid in raid_dict.items()]))

        # Ask the user to choose the raids
        await ctx.send("Which of these raids do you want to display in the timers command? (Enter the numbers separated by commas)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send('Sorry, you took too long.')
        else:
            # Save the server's preferences
            chosen_raids = [raid_dict[int(i)] for i in msg.content.split(",")]
            await self.config.guild(ctx.guild).raids.set(chosen_raids)
            await ctx.send(f"The server's preferences have been saved.")

    @timers.command()
    async def show(self, ctx):
        """Show the raid timers based on the server's preferences"""
        # Get the server's preferences
        chosen_raids = await self.config.guild(ctx.guild).raids()

        # Get the raid data
        data = self.get_web_data()

        # Filter the data based on the server's preferences
        data = [item for item in data if item["name"] in chosen_raids]

        # The rest of your code...