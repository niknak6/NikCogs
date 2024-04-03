from redbot.core import commands
import discord
import aiohttp
import json
import re

class PinFill(commands.Cog):
    """A cog for fetching Elemental Storms timers from WoWhead."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def elementalstorm(self, ctx):
        """Fetches and displays upcoming Elemental Storms timers."""
        url = "https://www.wowhead.com/today-in-wow"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    # Find the JSON data for the Elemental Storms using a regular expression
                    match = re.search(r'new WH\.Wow\.TodayInWow\(WH\.ge\(\'tiw-standalone\'\), (\[.*?\])\);', html, re.DOTALL)
                    if match:
                        data = json.loads(match.group(1))
                        # Iterate through the data to find the Elemental Storms section
                        for item in data:
                            if item['id'] == 'elemental-storms':
                                message = "Upcoming Elemental Storms:\n"
                                for line in item['content']['lines']:
                                    if 'class' in line and 'tiw-upcoming' in line['class']:
                                        zone = line['name']
                                        timer = line['ending']
                                        message += f"{zone}: {timer}\n"
                                await ctx.send(message)
                                return
                        await ctx.send("No upcoming Elemental Storms found.")
                    else:
                        await ctx.send("Failed to find the Elemental Storms data on WoWhead.")
                else:
                    await ctx.send("Failed to fetch data from WoWhead.")

async def setup(bot):
    bot.add_cog(PinFill(bot))
