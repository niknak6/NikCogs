import requests
from bs4 import BeautifulSoup
import discord
import textwrap
import json
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

            # Define a regex pattern to match the JSON data for the raid reset timers
            # Use a normal string literal and escape both the backslashes and the double quotes
            pattern = "[{\\\"id\\\":\\\"dungeons-and-raids\\\",.+?}(?=])];"

            # Search for the pattern in the web page source
            match = re.search(pattern, web_page_source)

            # Check if the pattern was found
            if match:
                # Get the matched substring
                json_data = match.group()

                # Convert the JSON data to a Python object
                data = json.loads(json_data)

                # Loop through the data
                for item in data:
                    # Get the name and region of the item
                    name = item["name"]
                    region = item["regionId"]

                    # Print the name and region
                    print(name, region)

                    # Get the groups of the item
                    groups = item["groups"]

                    # Loop through the groups
                    for group in groups:
                        # Get the content of the group
                        content = group["content"]

                        # Get the lines of the content
                        lines = content["lines"]

                        # Loop through the lines
                        for line in lines.values():
                            # Get the raid name, ending, and url of the line
                            raid_name = line["name"]
                            raid_ending = line["ending"]
                            raid_url = line["url"]

                            # Print the raid name, ending, and url
                            print(raid_name, raid_ending, raid_url)

                # Create an embed object
                embed = discord.Embed(title="Classic Raid Reset Timers", description="The raid reset timers for the classic season of discovery")

                # Add the name, raid name, ending, and url as fields
                embed.add_field(name=name, value=f"{raid_name}: {raid_ending} [More info]")

                # Send the embed to the channel
                await ctx.send(embed=embed)
            else:
                # Handle the error if the pattern was not found
                print("Error: No JSON data found")
        else:
            # Handle the error if the response status code is not 200
            print(f"Error: {response.status_code}")

            # Split the response.content into chunks of 2000 characters each
            chunks = textwrap.wrap(response.content, 2000)

            # Send each chunk as a code block to the channel
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")