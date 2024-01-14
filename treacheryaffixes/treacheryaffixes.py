import requests
from lxml.html import fromstring
from redbot.core import commands

class TreacheryAffixes(commands.Cog):
    """A cog that scrapes mythic plus information from a website"""

    def __init__(self, bot):
        self.bot = bot
        self.url = "https://mythicpl.us/"
        self.response = requests.get(self.url)
        self.root = fromstring(self.response.content)

    @commands.command()
    async def affixes(self, ctx):
        """Shows the affixes for the current, next, and week after next weeks"""
        # Find the h1 element with id="thisweekus"
        h1 = self.root.find(".//h1[@id='thisweekus']")
        # Get the text content of the h1 element
        current = h1.text_content()
        # Find the h4 element with id="nextweek"
        h4 = self.root.find(".//h4[@id='nextweek']")
        # Get the text content of the h4 element
        next = h4.text_content()
        # Find the h4 element with id="weekafternext"
        h4 = self.root.find(".//h4[@id='weekafternext']")
        # Get the text content of the h4 element
        weekafter = h4.text_content()
        # Format the text content with headings and line breaks
        text = f"**Current:**\n{current}\n\n**Next Week:**\n{next}\n\n**Week After Next:**\n{weekafter}"
        # Send the text to the channel
        await ctx.send(text)