# Import the required modules
import asyncio
from pyppeteer import launch
from redbot.core import commands
import json # Import the json module

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

        # Launch a headless browser and create a new page
        browser = await launch()
        page = await browser.newPage()

        # Set the headers for the page
        await page.setExtraHTTPHeaders(headers)

        # Go to the url and wait for the page to load
        await page.goto(url, waitUntil="networkidle0")

        # Evaluate a JavaScript expression on the page and get the result
        js_data = await page.evaluate("WH.Wow.TodayInWow.US")

        # Close the browser
        await browser.close()

        # Check if the js data is not None
        if js_data is None:
            # Handle the case when the js data is None
            await ctx.send("Sorry, I could not find the raid reset timers on the web page.")
        else:
            # Send the raid reset timers to the user
            await ctx.send("Here are the raid reset timers for classic wow (Eastern Time):")
            # Use a formatted string to display the pairs
            await ctx.send("\n".join(f"**{line['name']}**: {line['endingShort']}" for group in js_data for line in group["content"]["lines"].values()))

        # Check if debug dumping is enabled
        if self.debug:
            # Output the js data for debugging
            await ctx.send("Here is the js data:")
            js_data = json.dumps(js_data, indent=4)
            # Split the js data into chunks of 2000 characters
            chunks = [js_data[i:i+2000] for i in range(0, len(js_data), 2000)]
            # Send each chunk as a separate message
            for chunk in chunks:
                await ctx.send(chunk)
