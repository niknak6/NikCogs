import requests, discord, json, re, pytz
from datetime import datetime
from redbot.core import commands

class TreacheryTimers(commands.Cog):
    """A cog that fetches and parses web pages to get raid reset timers and WoW Mythic+ affixes by week"""

    def __init__(self, bot):
        self.bot = bot
        self.server_region = 'NA'
        self.selected_raids = ['Blackfathom Deeps']

    def fetch_and_parse(self, url, pattern):
        webpage_response = requests.get(url)
        if webpage_response.status_code != 200:
            return None

        matches = re.findall(pattern, webpage_response.text)
        if not matches:
            return None

        # If the pattern contains groups, matches will be a list of tuples.
        # In this case, we join each tuple into a string.
        if isinstance(matches[0], tuple):
            matches = [' '.join(match) for match in matches]

        return matches

    @commands.command()
    async def timers(self, ctx):
        """Fetches and parses the web page https://www.wowhead.com/classic and displays the classic raid reset timers"""
        # Use a non-greedy quantifier (+?) to match only one JSON object at a time
        raid_reset_matches = self.fetch_and_parse("https://www.wowhead.com/classic", r"\{\"ending\":\".+?\",\"endingShort\":\".+?\",\"endingUt\":\d+,\"name\":\".+?\",\"order\":\d+,\"url\":\".+?\"\}")
        if not raid_reset_matches:
            await ctx.send("No data can be found. Please check wowhead.com/classic to ensure times are visible. If the data is there, send a message to Nik.")
            return

        raid_reset_data = [json.loads(match) for match in raid_reset_matches]
        raid_reset_embed = discord.Embed(title="Classic Raid Reset Timers", description="")
        earliest_resets = {}

        for raid in raid_reset_data:
            raid_name, raid_ending_time = raid["name"], raid["ending"]
            if self.selected_raids and raid_name not in self.selected_raids:
                continue

            reset_time_utc = datetime.utcfromtimestamp(raid["endingUt"])
            reset_time_eastern = reset_time_utc.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('US/Eastern'))
            formatted_reset_time = reset_time_eastern.strftime('%m-%d-%Y %I:%M:%S %p %Z')

            if raid_name not in earliest_resets or self.server_region == 'EU':
                earliest_resets[raid_name] = (raid_ending_time, formatted_reset_time)

        [raid_reset_embed.add_field(name=raid_name, value=f"{raid_ending_time} (Resets at {formatted_reset_time})") for raid_name, (raid_ending_time, formatted_reset_time) in earliest_resets.items()]
        await ctx.send(embed=raid_reset_embed)

@commands.command()
async def mplus(self, ctx):
    """Fetches and parses the web page https://keystone.guru/affixes and displays the WoW Mythic+ affixes by week"""
    # Use a more specific pattern to match the date and the affixes
    affix_matches = self.fetch_and_parse("https://keystone.guru/affixes", r"(\d{4}/\w{3}/\d{2}).+?affix_icon_(.+?)\".+?affix_icon_(.+?)\".+?affix_icon_(.+?)\"")
    if not affix_matches:
        await ctx.send("No data can be found. Please check keystone.guru/affixes to ensure times are visible. If the data is there, send a message to Nik.")
        return

    affix_embed = discord.Embed(title="WoW Mythic+ Affixes by Week", description="")
    for match in affix_matches:
        # Split the match and use the groups to create the embed fields
        date, affix1, affix2, affix3 = match.split()
        affix_embed.add_field(name=date, value=f"+2: {affix1}, +7: {affix2}, +14: {affix3}", inline=False)

    await ctx.send(embed=affix_embed)