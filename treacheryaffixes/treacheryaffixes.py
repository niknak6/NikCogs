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
        # Get the text content of the h1 element using XPath
        current = " ".join(h1.xpath(".//text()"))
        # Find the h4 element with id="nextweek"
        h4 = self.root.find(".//h4[@id='nextweek']")
        # Get the text content of the h4 element using XPath
        next = " ".join(h4.xpath(".//text()"))
        # Find the h4 element with id="weekafternext"
        h4 = self.root.find(".//h4[@id='weekafternext']")
        # Get the text content of the h4 element using XPath
        weekafter = " ".join(h4.xpath(".//text()"))
        # Format the text content with headings and line breaks
        text = f"**Current:**\n{current}\n\n**Next Week:**\n{next}\n\n**Week After Next:**\n{weekafter}"
        # Send the text to the channel
        await ctx.send(text)