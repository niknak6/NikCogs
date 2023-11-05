# Import the necessary modules
import discord
from redbot.core import commands
import aiohttp  # Use aiohttp instead of requests
import humanize  # Use humanize to format the values and the timestamp
import json  # Import the json module
from datetime import datetime, timezone, timedelta  # Import the datetime module


# Define the cog class
class TreacheryToken(commands.Cog):
    """A cog that shows the WoW token price in the US region"""

    def __init__(self, bot):
        self.bot = bot

    # Define the command
    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the WoW token price in the US region"""

        # Get the json data from the website
        url = "https://data.wowtoken.app/token/history/us/48h.json"  # Use the url for the US region
        async with aiohttp.ClientSession() as session:  # Use async with to create a session and get the response
            async with session.get(url) as response:
                text = await response.text()  # Use response.text() to get the response content as a string
                data = json.loads(text)  # Use json.loads() to convert the string into a Python list

        # Check if the data variable is not None
        if data is not None:
            # Extract the relevant information
            price = data[-1]["value"]  # Get the current price from the last element of the list
            time = data[-1]["time"]  # Get the time of last change from the last element of the list
            change = data[-1]["value"] - data[-2]["value"]  # Get the last change from the difference between the last two elements of the list
            # Use a try-except block to get the 1 day low and high values by calling the get_low_high method with 1 day as the argument
            try:
                one_day_low, one_day_high = self.get_low_high(data, days=1)
            except TypeError:
                await ctx.send(
                    "Sorry, I could not get the 1 day low and high values for the WoW token price. Please try again later."
                )
                return
            # Use a try-except block to get the 7 day low and high values by calling the get_low_high method with 7 days as the argument
            try:
                seven_day_low, seven_day_high = self.get_low_high(data, days=7)
            except TypeError:
                await ctx.send(
                    "Sorry, I could not get the 7 day low and high values for the WoW token price. Please try again later."
                )
                return
            # Use a try-except block to get the 30 day low and high values by calling the get_low_high method with 30 days as the argument
            try:
                thirty_day_low, thirty_day_high = self.get_low_high(data, days=30)
            except TypeError:
                await ctx.send(
                    "Sorry, I could not get the 30 day low and high values for the WoW token price. Please try again later."
                )
                return

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
                price = humanize.intcomma(price)  # Use humanize.intcomma to add commas to the integers
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
            dt = datetime.fromisoformat(time)  # Convert the time string to a datetime object
            epoch = dt.replace(tzinfo=timezone.utc).timestamp()  # Convert the datetime object to a UNIX epoch time
            timestamp = humanize.naturaltime(epoch)  # Use humanize.naturaltime to format the UNIX epoch time

            # Create the embed message
            embed = discord.Embed(title=":coin: WoW Token Price in US :coin:", color=0x00ff00)
            change_emoji = "📈" if change > 0 else "📉"  # This is the emoji for the last change
            embed.add_field(name=discord.Embed.Empty, value=f"Current Price: {price} ({change_emoji} {change})")  # This is the merged field with the emoji
            embed.add_field(name=discord.Embed.Empty, value=f"Updated {timestamp}")  # This is the field without the small text
            embed.add_field(name=discord.Embed.Empty, value="\n", inline=False)  # This is the line break using the newline character
            one_day_low_emoji = "📈" if price > one_day_low else "📉"  # This is the emoji for the 1 day low
            embed.add_field(name=discord.Embed.Empty, value=f"1 Day Low {one_day_low_emoji}: {one_day_low}", inline=True)  # This is the field with the emoji
            one_day_high_emoji = "📈" if price < one_day_high else "📉"  # This is the emoji for the 1 day high
            embed.add_field(name=discord.Embed.Empty, value=f"1 Day High {one_day_high_emoji}: {one_day_high}", inline=True)  # This is the field with the emoji
            embed.add_field(name=discord.Embed.Empty, value="\n", inline=False)  # This is the line break using the newline character
            seven_day_low_emoji = "📈" if price > seven_day_low else "📉"  # This is the emoji for the 7 day low
            embed.add_field(name=discord.Embed.Empty, value=f"7 Day Low {seven_day_low_emoji}: {seven_day_low}", inline=True)  # This is the field with the emoji
            seven_day_high_emoji = "📈" if price < seven_day_high else "📉"  # This is the emoji for the 7 day high
            embed.add_field(name=discord.Embed.Empty, value=f"7 Day High {seven_day_high_emoji}: {seven_day_high}", inline=True)  # This is the field with the emoji
            embed.add_field(name=discord.Embed.Empty, value="\n", inline=False)  # This is the line break using the newline character
            thirty_day_low_emoji = "📈" if price > thirty_day_low else "📉"  # This is the emoji for the 30 day low
            embed.add_field(name=discord.Embed.Empty, value=f"30 Day Low {thirty_day_low_emoji}: {thirty_day_low}", inline=True)  # This is the field with the emoji
            thirty_day_high_emoji = "📈" if price < thirty_day_high else "📉"  # This is the emoji for the 30 day high
            embed.add_field(name=discord.Embed.Empty, value=f"30 Day High {thirty_day_high_emoji}: {thirty_day_high}", inline=True)  # This is the field with the emoji

            # Send the embed message
            await ctx.send(embed=embed)
        else:
            # Send an error message if the data variable is None
            await ctx.send("Sorry, I could not get the WoW token price for the US region. Please try again later.")

    # Define a helper method to get the low and high values for a given time interval
    def get_low_high(self, data, days):
        """Returns the low and high values for a given time interval from the data list"""
        # Get the datetime object for the start of the time interval
        start = datetime.now() - timedelta(days=days)
        # Convert the datetime object to a