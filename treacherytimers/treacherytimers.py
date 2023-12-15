# Import the required modules
from bs4 import BeautifulSoup
import requests
from redbot.core import commands
from datetime import datetime
import pytz

# Define the cog class
class TreacheryTimers(commands.Cog):
    """A cog that parses raid reset timers from wowhead.com/classic"""

    def __init__(self, bot):
        self.bot = bot
        # Define a variable to control debug dumping
        self.debug = False

    @commands.command()
    async def timers(self, ctx):
        """Shows the raid reset timers for classic wow"""

        # Define the url and the headers
        url = "https://www.wowhead.com/classic"
        headers = {"User-Agent": "Red-DiscordBot/3.5"}

        # Make a request and get the response
        response = requests.get(url, headers=headers)

        # Check if the response is successful
        if response.status_code == 200:
            # Parse the response content with beautifulsoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all the sections with the raid reset timers
            import re
            sections = soup.find_all("section", id=re.compile("^US-group-raidresets"))

            # Check if the sections are not empty
            if sections:
                # Initialize an empty list to store the timers and names
                mylist = [" ".join(section.stripped_strings) for section in sections]

                # Zip the list into pairs of name and timer
                pairs = zip(mylist[::2], mylist[1::2])

                # Send the timers and names to the user
                await ctx.send("Here are the raid reset timers for classic wow (Eastern Time):")
                # Use a formatted string to display the pairs
                await ctx.send("\n".join(f"{name}: {timer}" for name, timer in pairs))
            else:
                # Handle the case when the sections are empty
                await ctx.send("Sorry, I could not find any sections with the raid reset timers.")

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
