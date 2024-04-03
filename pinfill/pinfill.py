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
                    # Attempt to find the JSON data for the Elemental Storms using a regular expression
                    match = re.search(r'new WH\.Wow\.TodayInWow\(WH\.ge\(\'tiw-standalone\'\), (\[.*?\])\);', html, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        try:
                            data = json.loads(json_str)
                        except json.JSONDecodeError as e:
                            # If parsing fails, send back the part of the string that could not be parsed
                            error_pos = e.pos
                            error_snippet = json_str[max(0, error_pos - 50):error_pos + 50]
                            await ctx.send(f"Failed to parse the Elemental Storms data. Error near: ...{error_snippet}...")
                            return
                        
                        # Process the data to find the Elemental Storms section
                        found = False
                        for item in data:
                            if item['id'] == 'elemental-storms':
                                found = True
                                message = "Upcoming Elemental Storms:\n"
                                for line in item['content']['lines']:
                                    if 'class' in line and 'tiw-upcoming' in line['class']:
                                        zone = line['name']
                                        timer = line['ending']
                                        message += f"{zone}: {timer}\n"
                                await ctx.send(message)
                                break
                        if not found:
                            await ctx.send("No upcoming Elemental Storms found.")
                    else:
                        await ctx.send("Failed to find the Elemental Storms data on WoWhead.")
                else:
                    await ctx.send(f"Failed to fetch data from WoWhead. Status Code: {response.status}")

async def setup(bot):
    bot.add_cog(PinFill(bot))
