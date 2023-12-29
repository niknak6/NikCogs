import requests
import discord
import json
import re
import pytz
from datetime import datetime
from redbot.core import commands

class TreacheryTimers(commands.Cog):
    """A cog that fetches and parses web pages to get raid reset timers and WoW Mythic+ affixes by week"""

    def __init__(self, bot):
        self.bot = bot
        # Change the server region from NA to US
        self.server_region = 'US'
        self.selected_raids = ['Blackfathom Deeps']

    def fetch_and_parse(self, url, pattern):
        webpage_response = requests.get(url)
        if webpage_response.status_code != 200:
            return None

        match = re.search(pattern, webpage_response.text)
        if not match:
            return None

        # The first group in the match contains the JSON data
        json_data = match.group(1)
        # Parse the JSON data
        data = json.loads(json_data)

        return data

    @commands.command()
    async def timers(self, ctx):
        """Fetches and parses the web page https://www.wowhead.com/classic and displays the classic raid reset timers"""
        # Use a more specific regular expression to extract the JSON data from the string
        raid_reset_data = self.fetch_and_parse("https://www.wowhead.com/classic", r'new WH\.Wow\.TodayInWow\(WH\.ge\(\\'today-in-wow\\'\), (\[{"id":"dungeons-and-raids".*?"regionId":"\w{2}".*?"groups":\[{"id":"raidresets".*?"content":\{"lines":\{.*?\}\}\}\]\}\]\)+\);')
        if not raid_reset_data:
            await ctx.send("No data can be found. Please check wowhead.com/classic to ensure times are visible. If the data is there, send a message to Nik.")
            return

        raid_reset_embed = discord.Embed(title="Classic Raid Reset Timers", description="")
        earliest_resets = {}

        for region in raid_reset_data:
            if region["regionId"] != self.server_region:
                continue
            for group in region["groups"]:
                if group["id"] != "raidresets":
                    continue
                for raid_id, raid in group["content"]["lines"].items():
                    raid_name, raid_ending_time = raid["name"], raid["ending"]
                    if self.selected_raids and raid_name not in self.selected_raids:
                        continue

                    reset_time_utc = datetime.utcfromtimestamp(raid["endingUt"])
                    reset_time_eastern = reset_time_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
                    formatted_reset_time = reset_time_eastern.strftime('%m-%d-%Y %I:%M:%S %p %Z')

                    if raid_name not in earliest_resets:
                        earliest_resets[raid_name] = (raid_ending_time, formatted_reset_time)

        [raid_reset_embed.add_field(name=raid_name, value=f"{raid_ending_time} (Resets at {formatted_reset_time})") for raid_name, (raid_ending_time, formatted_reset_time) in earliest_resets.items()]
        await ctx.send(embed=raid_reset_embed)