from redbot.core import commands
import discord
import aiohttp
import json

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
                    start_index = html.find('[{"class":"elemental-storm')
                    end_index = html.find('}]', start_index) + 2
                    if start_index != -1 and end_index != -1:
                        json_str = html[start_index:end_index]
                        try:
                            data = json.loads(json_str)
                            message = "Upcoming Elemental Storms:\n"
                            for item in data:
                                if 'class' in item and 'tiw-upcoming' in item['class']:
                                    zone = item['name']
                                    timer = item['ending']
                                    message += f"{zone}: {timer}\n"
                            await ctx.send(message)
                        except json.JSONDecodeError as e:
                            await ctx.send("Failed to parse the Elemental Storms data.")
                    else:
                        await ctx.send("Failed to find the Elemental Storms data on WoWhead.")
                else:
                    await ctx.send(f"Failed to fetch data from WoWhead. Status Code: {response.status}")

async def setup(bot):
    bot.add_cog(PinFill(bot))
