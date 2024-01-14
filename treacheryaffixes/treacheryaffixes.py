# Import the required modules
from redbot.core import commands
import requests
from bs4 import BeautifulSoup

# Define the cog class
class TreacheryAffixes(commands.Cog):
    """A cog that shows the current and upcoming affixes for Mythic+ dungeons."""

    def __init__(self, bot):
        self.bot = bot
        self.url = "https://mythicpl.us/" # The website to scrape from
        self.headers = {"User-Agent": "Red-DiscordBot/3.5.5"} # A custom user agent to avoid blocking

    @commands.command()
    async def affixes(self, ctx):
        """Shows the current and upcoming affixes for Mythic+ dungeons."""
        # Send a GET request to the website and parse the HTML response
        response = requests.get(self.url, headers=self.headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the elements that contain the affixes
        current_affixes = soup.find("h1", id="thisweekus").text.strip()
        next_week_affixes = soup.find("h4", id="nextweek").text.strip()
        week_after_next_affixes = soup.find("h4", id="weekafternext").text.strip()

        # Format the output message
        output = f"**Current:**\n{current_affixes}\n\n"
        output += f"**Next Week:**\n{next_week_affixes}\n\n"
        output += f"**Week After Next:**\n{week_after_next_affixes}"

        # Send the output message to the channel
        await ctx.send(output)