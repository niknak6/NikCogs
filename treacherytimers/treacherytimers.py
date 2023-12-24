import requests
from bs4 import BeautifulSoup
import discord
import textwrap
import json
import re
from redbot.core import commands

class TreacheryTimers(commands.Cog):
    """A cog that downloads and parses a web page"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timers(self, ctx):
        """Downloads and parses the web page https://www.wowhead.com/classic and shows the classic raid reset timers"""

        # Define the URL to download
        url = "https://www.wowhead.com/classic"

        # Send a GET request to the URL and store the response
        response = requests.get(url)

        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            # Get the response content as a string
            web_page_source = response.text

            # Define a regex pattern to match the lines with the ending, endingShort, endingUt, and name fields in the source
            # Use a raw string literal and escape the double quotes
            pattern = r"\{\\\"ending\\\":\\\".+?\\\",\\\"endingShort\\\":\\\".+?\\\",\\\"endingUt\\\":\\d+,\\\"name\\\":\\\".+?\\\",.+?\}"

            # Find all the matches of the pattern in the web page source
            matches = re.findall(pattern, web_page_source)

            # Check if any matches were found
            if matches:
                # Create an empty list to store the parsed data
                data = []

                # Loop through the matches
                for match in matches:
                    # Remove the backslashes from the matched string
                    match = match.replace("\\", "")

                    # Convert the matched string to a Python object using json.loads()
                    item = json.loads(match)

                    # Append the item to the data list
                    data.append(item)

                # Create an embed object
                embed = discord.Embed(title="Classic Raid Reset Timers", description="The raid reset timers for the classic season of discovery")

                # Loop through the data
                for item in data:
                    # Get the name, raid name, ending, and url of the item
                    name = item["name"]
                    raid_name = item["name"]
                    raid_ending = item["ending"]
                    raid_url = item["url"]

                    # Add the name, raid name, ending, and url as fields
                    embed.add_field(name=name, value=f"{raid_name}: {raid_ending} More info")

                # Send the embed to the channel
                await ctx.send(embed=embed)
            else:
                # Handle the error if no matches were found
                print("Error: No JSON data found")
        else:
            # Handle the error if the response status code is not 200
            print(f"Error: {response.status_code}")

            # Split the response.content into chunks of 2000 characters each
            chunks = textwrap.wrap(response.content, 2000)

            # Send each chunk as a code block to the channel
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")