import requests
import discord
import textwrap
import json
import re
from datetime import datetime
import pytz
from redbot.core import commands

class TreacheryTimers(commands.Cog):
    """A cog that downloads and parses a web page"""

    def __init__(self, bot):
        self.bot = bot
        self.region = 'NA'  # Set your region here
        self.raid_filter = ['Blackfathom Deeps']  # Set your raid filter here

    @commands.command()
    async def timers(self, ctx):
        """Downloads and parses the web page https://www.wowhead.com/classic and shows the classic raid reset timers"""

        url = "https://www.wowhead.com/classic"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            chunks = textwrap.wrap(response.content, 2000)
            for chunk in chunks:
                await ctx.send(f"```{chunk}```")
            return

        pattern = r"\{\"ending\":\".+?\",\"endingShort\":\".+?\",\"endingUt\":\d+,\"name\":\".+?\",.+?\}"
        matches = re.findall(pattern, response.text)

        if not matches:
            print("Error: No JSON data found")
            return

        data = [json.loads(match) for match in matches]
        embed = discord.Embed(title="Classic Raid Reset Timers", description="")
        first_occurrences = {}

        for item in data:
            raid_name = item["name"]
            raid_ending = item["ending"]

            if self.raid_filter and raid_name not in self.raid_filter:
                continue

            reset_time_utc = datetime.utcfromtimestamp(item["endingUt"])
            eastern = pytz.timezone('US/Eastern')
            reset_time_eastern = reset_time_utc.replace(tzinfo=pytz.utc).astimezone(eastern)
            reset_time_str = reset_time_eastern.strftime('%m-%d-%Y %I:%M:%S %p %Z')

            if raid_name not in first_occurrences or self.region == 'EU':
                first_occurrences[raid_name] = (raid_ending, reset_time_str)

        for raid_name, (raid_ending, reset_time_str) in first_occurrences.items():
            embed.add_field(name=raid_name, value=f"{raid_ending} (Resets at {reset_time_str})")

        await ctx.send(embed=embed)