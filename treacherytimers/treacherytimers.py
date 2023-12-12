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

            # Find the section with the raid reset timers
            section = soup.find("section", id="US-group-raidresets")

            # Find the link with the Blackfathom Deeps raid
            link = section.find("a", href="/classic/zone=719/blackfathom-deeps")

            # Get the timer as a timestamp
            timer = link.parent["data-ut"]

            # Convert the timestamp to a datetime object
            timer = datetime.fromtimestamp(int(timer))

            # Convert the datetime object to eastern time
            utc = pytz.utc
            eastern = pytz.timezone("US/Eastern")
            timer = utc.localize(timer).astimezone(eastern)

            # Format the datetime object as a string
            timer = timer.strftime("%Y-%m-%d %H:%M:%S")

            # Send the timer to the user
            await ctx.send(f"The reset timer for Blackfathom Deeps is {timer} (Eastern Time).")

        else:
            # Send an error message if the response is not successful
            await ctx.send(f"Sorry, I could not get the data from the remote host. The status code is {response.status_code}.")
