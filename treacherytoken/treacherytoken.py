# Import the necessary modules
import discord
from redbot.core import commands
import aiohttp # Use aiohttp instead of requests
import humanize # Use humanize to format the values and the timestamp

# Define the cog class
class TreacheryToken(commands.Cog):
    """A cog that shows the WoW token price in a specified region"""

    def __init__(self, bot):
        self.bot = bot

    # Define the command
    @commands.command()
    async def wowtoken(self, ctx, region: str = "us"):
        """Shows the WoW token price in a specified region"""

        # Validate the region argument
        valid_regions = ["us", "eu", "cn", "tw", "kr"]
        if region.lower() not in valid_regions:
            await ctx.send(f"Invalid region: {region}. Please choose one of these: {', '.join(valid_regions)}.")
            return

        # Get the json data from the website
        url = "https://wowtokenprices.com/current_prices.json"
        async with aiohttp.ClientSession() as session: # Use async with to create a session and get the response
            async with session.get(url) as response:
                data = await response.json() # Use await to get the json data

        # Extract the relevant information
        price = data[region.lower()]["current_price"]
        time = data[region.lower()]["time_of_last_change_unix_epoch"]
        change = int(data[region.lower()]["last_change"]) # This is the line that converts the string to an integer
        one_day_low = data[region.lower()]["1_day_low"]
        one_day_high = data[region.lower()]["1_day_high"]
        seven_day_low = data[region.lower()]["7_day_low"]
        seven_day_high = data[region.lower()]["7_day_high"]
        thirty_day_low = data[region.lower()]["30_day_low"]
        thirty_day_high = data[region.lower()]["30_day_high"]

        # Convert the values to integers
        try:
            price = int(price)
        except ValueError:
            price = "No Data"
        try:
            one_day_low = int(one_day_low)
        except ValueError:
            one_day_low = "No Data"
        try:
            one_day_high = int(one_day_high)
        except ValueError:
            one_day_high = "No Data"
        try:
            seven_day_low = int(seven_day_low)
        except ValueError:
            seven_day_low = "No Data"
        try:
            seven_day_high = int(seven_day_high)
        except ValueError:
            seven_day_high = "No Data"
        try:
            thirty_day_low = int(thirty_day_low)
        except ValueError:
            thirty_day_low = "No Data"
        try:
            thirty_day_high = int(thirty_day_high)
        except ValueError:
            thirty_day_high = "No Data"

        # Format the values with commas
        if price != "No Data":
            price = humanize.intcomma(price) # Use humanize.intcomma to add commas to the integers
        if one_day_low != "No Data":
            one_day_low = humanize.intcomma(one_day_low)
        if one_day_high != "No Data":
            one_day_high = humanize.intcomma(one_day_high)
        if seven_day_low != "No Data":
            seven_day_low = humanize.intcomma(seven_day_low)
        if seven_day_high != "No Data":
            seven_day_high = humanize.intcomma(seven_day_high)
        if thirty_day_low != "No Data":
            thirty_day_low = humanize.intcomma(thirty_day_low)
        if thirty_day_high != "No Data":
            thirty_day_high = humanize.intcomma(thirty_day_high)

        # Format the timestamp with a human-readable format
        timestamp = humanize.naturaltime(time) # Use humanize.naturaltime to convert the unix epoch time to a relative time

        # Create the embed message
        embed = discord.Embed(title=f":coin: WoW Token Price in {region.upper()} :coin:", color=0x00ff00)
        change_emoji = "📈" if change > 0 else "📉" # This is the emoji for the last change
        embed.add_field(name=discord.Embed.Empty, value=f"Current Price: {price} ({change_emoji} {change})") # This is the merged field with the emoji
        embed.add_field(name=discord.Embed.Empty, value=f"Updated {timestamp}") # This is the field without the small text
        embed.add_field(name=discord.Embed.Empty, value="\n", inline=False) # This is the line break using the newline character
        one_day_low_emoji = "📈" if price > one_day_low else "📉" # This is the emoji for the 1 day low
        embed.add_field(name=discord.Embed.Empty, value=f"1 Day Low {one_day_low_emoji}: {one_day_low}", inline=True) # This is the field with the emoji
        one_day_high_emoji = "📈" if price < one_day_high else "📉" # This is the emoji for the 1 day high
        embed.add_field(name=discord.Embed.Empty, value=f"1 Day High {one_day_high_emoji}: {one_day_high}", inline=True) # This is the field with the emoji
        embed.add_field(name=discord.Embed.Empty, value="\n", inline=False) # This is the line break using the newline character
        seven_day_low_emoji = "📈" if price > seven_day_low else "📉" # This is the emoji for the 7 day low
        embed.add_field(name=discord.Embed.Empty, value=f"7 Day Low {seven_day_low_emoji}: {seven_day_low}", inline=True) # This is the field with the emoji
        seven_day_high_emoji = "📈" if price < seven_day_high else "📉" # This is the emoji for the 7 day high
        embed.add_field(name=discord.Embed.Empty, value=f"7 Day High {seven_day_high_emoji}: {seven_day_high}", inline=True) # This is the field with the emoji
        embed.add_field(name=discord.Embed.Empty, value="\n", inline=False) # This is the line break using the newline character
        thirty_day_low_emoji = "📈" if price > thirty_day_low else "📉" # This is the emoji for the 30 day low
        embed.add_field(name=discord.Embed.Empty, value=f"30 Day Low {thirty_day_low_emoji}: {thirty_day_low}", inline=True) # This is the field with the emoji
        thirty_day_high_emoji = "📈" if price < thirty_day_high else "📉" # This is the emoji for the 30 day high
        embed.add_field(name=discord.Embed.Empty, value=f"30 Day High {thirty_day_high_emoji}: {thirty_day_high}", inline=True) # This is the field with the emoji

        # Send the embed message
        await ctx.send(embed=embed)
