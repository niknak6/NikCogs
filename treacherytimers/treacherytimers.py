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
            # Parse the response content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all the elements that have the class 'today-in-wow'
            today_in_wow_elements = soup.find_all(class_="today-in-wow")

            # Loop through the elements
            for element in today_in_wow_elements:
                # Find the element that has the id 'dungeons-and-raids'
                dungeons_and_raids_element = element.find(id="dungeons-and-raids")

                # Find all the elements that have the class 'lines'
                lines_elements = dungeons_and_raids_element.find_all(class_="lines")

                # Loop through the elements
                for lines_element in lines_elements:
                    # Get the value of the 'name' attribute
                    name = lines_element.get("name")

                    # Print the name
                    print(name)

                    # Find all the elements that have the class 'line'
                    line_elements = lines_element.find_all(class_="line")

                    # Loop through the elements
                    for line_element in line_elements:
                        # Get the value of the 'name' attribute
                        raid_name = line_element.get("name")

                        # Get the value of the 'ending' attribute
                        raid_ending = line_element.get("ending")

                        # Get the value of the 'url' attribute
                        raid_url = line_element.get("url")

                        # Print the raid name, ending, and url
                        print(raid_name, raid_ending, raid_url)

            # Create an embed object
            embed = discord.Embed(title="Classic Raid Reset Timers", description="The raid reset timers for the classic season of discovery")

            # Add the name, raid name, ending, and url as fields
            embed.add_field(name=name, value=f"{raid_name}: {raid_ending} [More info](https://docs.python.org/3/library/html.parser.html)")

            # Send the embed to the channel
            await ctx.send(embed=embed)
        else:
            # Handle the error if the response status code is not 200
            print(f"Error: {response.status_code}")

            # Split the response.content into chunks of 2000 characters each
            chunks = textwrap.wrap(response.content, 2000)

            # Send each chunk as a code block to the channel
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")