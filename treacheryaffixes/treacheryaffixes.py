from redbot.core import commands
import aiohttp
from bs4 import BeautifulSoup
from datetime import datetime

# Define constants for the URLs and the affix icon prefix
CURRENT_WEEK_URL = "https://keystone.guru/affixes"
FUTURE_WEEKS_URL = "https://keystone.guru/affixes?offset=1"
AFFIX_ICON_PREFIX = "affix_icon_"

class TreacheryAffixes(commands.Cog):
    """A cog that displays world of warcraft m+ data"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def affixes(self, ctx):
        """Displays the current week and the future weeks affixes"""
        # Get the current week and the future weeks affixes
        current_week, future_weeks = await self.fetch_affix_data()
        # Format and send the data as a message
        await ctx.send(f"**Current Week:**\n{current_week}\n**Future Weeks:**\n{future_weeks}")

    async def fetch_affix_data(self):
        """Sends GET requests to both URLs, parses the HTML tables, and returns the affix data"""
        # Create an asynchronous session and send GET requests to both URLs
        async with aiohttp.ClientSession() as session, session.get(CURRENT_WEEK_URL) as current_response, session.get(FUTURE_WEEKS_URL) as future_response:
            # Parse the response texts and find the table body elements
            current_table = BeautifulSoup(await current_response.text(), "lxml").select_one("tbody")
            future_table = BeautifulSoup(await future_response.text(), "lxml").select_one("tbody")
            # Parse the last row for the current week and get the date and the affixes
            current_date, current_affixes = self.parse_row(current_table.select("tr")[-1])
            # Parse the rows for the future weeks and get the dates and the affixes
            future_data = [self.parse_row(row) for row in future_table.select("tr") if "confirmed" not in row.get("class")]
            # Format and return the data as strings
            return f"{current_date}: {', '.join(current_affixes)}", "\n".join(f"{date}: {', '.join(affixes)}" for date, affixes in future_data)

    def parse_row(self, row):
        """Parses a table row and returns the date and the affixes"""
        # Get the class attribute of the row
        row_class = row.get("class")
        # Get the text from the first column or the span element
        date = row.find("td", class_="first_column").text.strip() if "timewalking" in row_class else row.find("span").text.strip()
        # Convert and format the date string if it is not 'Legion timewalking'
        date = datetime.strptime(date, "%Y/%b/%d").date().strftime("%m/%d/%y") if date != "Legion timewalking" else date
        # Find the affix divs and get their last class name without the affix icon prefix
        affixes = [div["class"][-1].replace(AFFIX_ICON_PREFIX, "").capitalize() for div in row.select(f"div[class*={AFFIX_ICON_PREFIX}]")]
        # Return the date and the affixes
        return date, affixes
