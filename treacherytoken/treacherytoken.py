# Import the necessary modules
import discord
from redbot.core import commands
import aiohttp  # Use aiohttp instead of requests
import humanize  # Use humanize to format the values and the timestamp
import json  # Import the json module
from datetime import datetime, timezone, timedelta  # Import the datetime module
import logging  # Import the logging module

# Get the logger object
logger = logging.getLogger("red.treacherytoken")

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
            # Define a list of time intervals in days
            intervals = [1, 7, 30]
            # Initialize a dictionary to store the low and high values for each time interval
            low_high = {}
            # Loop through the time intervals
            for days in intervals:
                # Use a try-except block to get the low and high values by calling the get_low_high method with the days as the argument
                try:
                    low_high[days] = self.get_low_high(data, days)
                except TypeError as e:
                    # Print the data list and the start time to the console
                    logger.debug(f"data: {data}")
                    start = datetime.now() - timedelta(days=days)
                    logger.debug(f"start: {start}")
                    # Print the type and value of the exception to the console
                    logger.debug(f"exception type: {type(e)}")
                    logger.debug(f"exception value: {e}")
                    # Send an error message to the user
                    await ctx.send(
                        f"Sorry, I could not get the {days} day low and high values for the WoW token price. Please try again later."
                    )
                    return

            # Convert the values to integers or strings
            price = self.convert_value(price)
            change = self.convert_value(change)  # Convert the change variable to an integer
            for days in intervals:
                low_high[days] = tuple(self.convert_value(v) for v in low_high[days])

            # Format the values with commas
            price = self.format_value(price)
            change = self.format_value(change)
            for days in intervals:
                low_high[days] = tuple(self.format_value(v) for v in low_high[days])

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
            # Loop through the time intervals
            for days in intervals:
                # Get the low and high values for the current time interval
                low, high = low_high[days]
                # Get the emojis for the low and high values
                low_emoji = "📈" if price > low else "📉"  # This is the emoji for the low value
                high_emoji = "📈" if price < high else "📉"  # This is the emoji for the high value
                # Add the fields with the emojis
                embed.add_field(name=discord.Embed.Empty, value=f"{days} Day Low {low_emoji}: {low}", inline=True)  # This is the field with the emoji
                embed.add_field(name=discord.Embed.Empty, value=f"{days} Day High {high_emoji}: {high}", inline=True)  # This is the field with the emoji
                # Add the line break using the newline character
                embed.add_field(name=discord.Embed.Empty, value="\n", inline=False)

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
        # Convert the datetime object to a ISO 8601 string
        start = start.isoformat()
        # Initialize the low and high values
        low = None
        high = None
        # Loop through the data list
        for item in data:
            # Check if the item's time is within the time interval
            if item["time"] >= start:
                # Check if the item's value is lower than the current low value
                if low is None or item["value"] < low:
                    # Update the low value
                    low = item["value"]
                # Check if the item's value is higher than the current high value
                if high is None or item["value"] > high:
                    # Update the high value
                    high = item["value"]
        # Return the low and high values as a tuple
        return (low, high)

    # Define a helper method to convert the values to integers or strings
    def convert_value(self, value):
        """Returns the value as an integer or a string"""
        # Try to convert the value to an integer
        try:
            value = int(value)
        except ValueError:
            # If the conversion fails, use "No Data" as the default value
            value = "No Data"
        # Return the converted value
        return value

    # Define a helper method to format the values with commas
    def format_value(self, value):
        """Returns the value as a formatted string with commas"""
        # Check if the value is an integer
        if isinstance(value, int):
            # Use humanize.intcomma to add commas to the integer
            value = humanize.intcomma(value)
        # Return the formatted value
        return value
