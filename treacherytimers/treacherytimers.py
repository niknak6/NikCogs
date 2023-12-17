# Import the required modules
from bs4 import BeautifulSoup
import requests
from redbot.core import commands
from datetime import datetime
import pytz

# Define the cog class
class TreacheryTimers(commands.Cog):
    """A cog that parses raid reset timers from classicraidreset.com/US/SoD"""

    def __init__(self, bot):
        self.bot = bot
        # Define a variable to control debug dumping
        self.debug = False

    @commands.command()
    async def timers(self, ctx):
        """Shows the raid reset timers for classic SoD (Eastern Time)"""

        # Define the url and the headers
        url = "https://classicraidreset.com/US/SoD"
        headers = {"User-Agent": "Red-DiscordBot/3.5"}

        # Make a request and get the response
        response = requests.get(url, headers=headers)

        # Check if the response is successful
        if response.status_code == 200:
            # Parse the response content with beautifulsoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all the divs with the raid reset timers
            def is_raid_reset(tag):
                return tag.name == "div" and tag.has_attr("id") and tag["id"][0].isdigit()

            sections = soup.find_all(is_raid_reset)

            # Check if the sections are not empty
            if sections:
                # Initialize an empty list to store the timers and names
                mylist = [section.find("span").text for section in sections]

                # Send the timers and names to the user
                await ctx.send("Here are the raid reset timers for classic SoD (Eastern Time):")
                # Use a formatted string to display the list
                await ctx.send("\n".join(mylist))
            else:
                # Handle the case when the sections are empty
                await ctx.send("Sorry, I could not find any divs with the raid reset timers.")

        else:
            # Send an error message if the response is not successful
            await ctx.send(f"Sorry, I could not get the data from the remote host. The status code is {response.status_code}.")

        # Check if debug dumping is enabled
        if self.debug:
            # Output the response content for debugging
            await ctx.send("Here is the response content:")
            content = soup.prettify()
            # Split the content into chunks of 2000 characters
            chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
            # Send each chunk as a separate message
            for chunk in chunks:
                await ctx.send(chunk)
