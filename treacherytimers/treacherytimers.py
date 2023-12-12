# Import the required modules
from redbot.core import commands
import requests
from bs4 import BeautifulSoup
import datetime
import importlib # Import the importlib module

# Define the cog class
class TreacheryTimers(commands.Cog):
    """A cog that shows the raid reset timers for WoW Classic"""

    def __init__(self, bot):
        self.bot = bot
        self.url = "https://www.wowhead.com/classic" # The remote host URL
        self.raid = "Blackfathom Deeps" # The raid name
        self.section_id = "US-group-raidresets" # The section id in the HTML
        self.line_id = "US-group-raidresets-line-7" # The line id in the HTML

    @commands.command()
    async def timers(self, ctx):
        """Shows the timer for Blackfathom Deeps"""
        # Get the HTML content from the URL
        response = requests.get(self.url)
        # Parse the HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        # Find the section element by id
        section = soup.find(id=self.section_id)
        # Find the line element by id
        line = section.find(id=self.line_id)
        # Find the timer element by data-ut attribute
        timer = line.find(attrs={"data-ut": True})
        # Get the data-ut value as an integer
        timestamp = int(timer["data-ut"])
        # Convert the timestamp to a datetime object
        dt = datetime.datetime.fromtimestamp(timestamp)
        # Format the datetime object as a string
        dt_str = dt.strftime("%Y-%m-%d %H:%M:%S")
        # Send the message to the user
        await ctx.send(f"The timer for {self.raid} is {dt_str}")

        # Import the module by its name as a string
        homePageLib = importlib.import_module("homePageLib")
        # Use the module object to access its attributes
        page = homePageLib.HomePage()
        print(page)
