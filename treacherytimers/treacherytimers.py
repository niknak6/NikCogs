import requests, discord, json, re, pytz
from datetime import datetime
from redbot.core import commands

class TreacheryTimers(commands.Cog):
    """A cog that downloads and parses a web page"""

    def __init__(self, bot):
        self.bot = bot
        self.region = 'NA'
        self.raid_filter = ['Blackfathom Deeps']

    @commands.command()
    async def timers(self, ctx):
        """Downloads and parses the web page https://www.wowhead.com/classic and shows the classic raid reset timers"""
        response = requests.get("https://www.wowhead.com/classic")
        if response.status_code != 200:
            await ctx.send("No data can be found. Please check wowhead.com/classic. If the data is there, send a message to Nik.")
            return

        pattern = r"\{\"ending\":\".+?\",\"endingShort\":\".+?\",\"endingUt\":\d+,\"name\":\".+?\",.+?\}"
        matches = re.findall(pattern, response.text)
        if not matches:
            await ctx.send("No data can be found. Please check wowhead.com/classic. If the data is there, send a message to Nik.")
            return

        data = [json.loads(match) for match in matches]
        embed = discord.Embed(title="Classic Raid Reset Timers", description="")
        first_occurrences = {}

        for item in data:
            raid_name, raid_ending = item["name"], item["ending"]
            if self.raid_filter and raid_name not in self.raid_filter:
                continue

            reset_time_utc = datetime.utcfromtimestamp(item["endingUt"])
            reset_time_eastern = reset_time_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
            reset_time_str = reset_time_eastern.strftime('%m-%d-%Y %I:%M:%S %p %Z')

            if raid_name not in first_occurrences or self.region == 'EU':
                first_occurrences[raid_name] = (raid_ending, reset_time_str)

        [embed.add_field(name=raid_name, value=f"{raid_ending} (Resets at {reset_time_str})") for raid_name, (raid_ending, reset_time_str) in first_occurrences.items()]
        await ctx.send(embed=embed)