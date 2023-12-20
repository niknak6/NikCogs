# Import the necessary libraries
import asyncio
import discord
from redbot.core import commands
from pyppeteer import launch

# Define a class for the cog
class RaidTimerCog(commands.Cog):
    """A cog that displays raid timers and dates from https://classicraidreset.com/US/SoD"""

    def __init__(self, bot):
        self.bot = bot

    # Define a command to get the raid timers and dates
    @commands.command()
    async def raidtimer(self, ctx):
        """Get the raid timers and dates from https://classicraidreset.com/US/SoD"""

        # Launch a browser and a page
        browser = await launch()
        page = await browser.newPage()

        # Go to the website and wait for the calendar to load
        await page.goto("https://classicraidreset.com/US/SoD")
        await page.waitForSelector("#calendar-element")

        # Get the HTML content of the calendar
        calendar = await page.querySelectorEval("#calendar-element", "element => element.innerHTML")

        # Close the browser
        await browser.close()

        # Send the calendar as a message
        await ctx.send(f"Here is the raid timer and date calendar from https://classicraidreset.com/US/SoD:\n```html\n{calendar}\n```")