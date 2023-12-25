import requests
import discord
import textwrap
import json
import re
from datetime import datetime
import pytz
from redbot.core import commands

class TreacheryTimers(commands.Cog):
    """A cog that downloads and parses a web page"""

    def __init__(self, bot):
        self.bot = bot
        self.region = 'NA'  # Set your region here
        self.raid_filter = ['Blackfathom Deeps']  # Set your raid filter here

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
            pattern = r"\{\"ending\":\".+?\",\"endingShort\":\".+?\",\"endingUt\":\d+,\"name\":\".+?\",.+?\}"

            # Find all the matches of the pattern in the web page source
            matches = re.findall(pattern, web_page_source)

            # Check if any matches were found
            if matches:
                # Create an empty list to store the parsed data
                data = []

                # Loop through the matches
                for match in matches:
                    # Convert the matched string to a Python object using json.loads()
                    item = json.loads(match)

                    # Append the item to the data list
                    data.append(item)

                # Create an embed object
                embed = discord.Embed(title="Classic Raid Reset Timers", description="")

                # Create a dictionary to store the first occurrence of each raid
                first_occurrences = {}

                # Loop through the data
                for item in data:
                    # Get the name, raid name, ending, and url of the item
                    raid_name = item["name"]
                    raid_ending = item["ending"]

                    # If the raid filter is not empty and the raid name is not in the filter, skip this item
                    if self.raid_filter and raid_name not in self.raid_filter:
                        continue

                    # Convert the endingUt timestamp to a datetime object
                    reset_time_utc = datetime.utcfromtimestamp(item["endingUt"])

                    # Convert the UTC time to Eastern Time
                    eastern = pytz.timezone('US/Eastern')
                    reset_time_eastern = reset_time_utc.replace(tzinfo=pytz.utc).astimezone(eastern)

                    # Format the reset time
                    reset_time_str = reset_time_eastern.strftime('%m-%d-%Y %I:%M:%S %p %Z')

                    # Check if the raid name is already in the first_occurrences dictionary
                    if raid_name not in first_occurrences:
                        # If it's not, add it to the dictionary
                        first_occurrences[raid_name] = (raid_ending, reset_time_str)
                    else:
                        # If it is, check the region
                        if self.region == 'NA':
                            # If the region is 'NA', continue to the next item
                            continue
                        elif self.region == 'EU':
                            # If the region is 'EU', update the dictionary with the new ending and reset time
                            first_occurrences[raid_name] = (raid_ending, reset_time_str)

                # Loop through the first_occurrences dictionary
                for raid_name, (raid_ending, reset_time_str) in first_occurrences.items():
                    # Add the raid name, ending, and reset time as fields
                    embed.add_field(name=raid_name, value=f"{raid_ending} (Resets at {reset_time_str})")

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