import requests
from discord.ext import commands

class TreacheryTimers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timers(self, ctx):
        url = "https://www.wowhead.com/classic"
        response = requests.get(url)
        html_source = response.text

        # Split the source into 2000 character chunks
        chunks = [html_source[i:i+2000] for i in range(0, len(html_source), 2000)]

        # Send each chunk to the channel
        for chunk in chunks:
            await ctx.send(f'```{chunk}```')

def setup(bot):
    bot.add_cog(TreacheryTimers(bot))