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

            # Find the section with the raid reset timers
            # Use the class and data-group attributes instead of the id attribute
            section = soup.find("section", class_="group", attrs={"data-group": "US"})

            # Check if the section exists
            if section is not None:
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
                # Handle the case when the section is not found
                await ctx.send("Sorry, I could not find the section with the raid reset timers.")

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
