from redbot.core import commands
import discord
import aiohttp
from bs4 import BeautifulSoup

class TreacheryNews(commands.Cog):
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
                    soup = BeautifulSoup(html, 'html.parser')
                    # Find the section containing Elemental Storms information
                    storms_section = soup.find('section', {'data-tiw-section': 'group-elemental-storms'})
                    if storms_section:
                        upcoming_storms = storms_section.find_all('section', class_='tiw-line-name elemental-storm tiw-upcoming')
                        upcoming_times = storms_section.find_all('section', class_='tiw-line-ending elemental-storm tiw-upcoming tiw-active')
                        if upcoming_storms and upcoming_times:
                            message = "Upcoming Elemental Storms:\n"
                            for storm, time in zip(upcoming_storms, upcoming_times):
                                zone = storm.span.text
                                timer = time.text
                                message += f"{zone}: {timer}\n"
                            await ctx.send(message)
                        else:
                            await ctx.send("No upcoming Elemental Storms found.")
                    else:
                        await ctx.send("Failed to find the Elemental Storms section on WoWhead.")
                else:
                    await ctx.send("Failed to fetch data from WoWhead.")

async def setup(bot):
    bot.add_cog(TreacheryNews(bot))
