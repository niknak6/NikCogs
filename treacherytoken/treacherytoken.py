import time
from redbot.core import commands
import aiohttp # a library for making asynchronous HTTP requests
import pandas as pd # a library for data analysis and manipulation
import discord # a library for interacting with the Discord API
from datetime import datetime, timedelta # a module for working with dates and times
import orjson as json # a library for fast JSON encoding and decoding
import random # a module for generating random numbers
from aiohttp import ClientTimeout # a class for setting the timeout for HTTP requests

# Create a function that creates and returns a new session object
def get_session():
    # Create a cookie jar object to store and send cookies
    jar = aiohttp.CookieJar(unsafe=True)
    # Create and return a new session object with the cookie jar and no timeout
    # A session object allows to make multiple requests with the same settings
    return aiohttp.ClientSession(cookie_jar=jar, timeout=ClientTimeout(total=None))

class TreacheryToken(commands.Cog):
    """A cog that shows the price of the wow token"""

    def __init__(self, bot):
        self.bot = bot
        # Create a global dictionary to store the tasks
        self.tasks = {}

    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the current, weekly, monthly, 6 month and 1 year high and low price of the wow token in US region"""
        # Get the start time of processing the data
        start_time = time.perf_counter()

        # Send a temporary message with the loading text
        loading_message = await ctx.send("Loading WoW Token Information...")

        # Get the json data from the url
        url = "https://data.wowtoken.app/token/history/us/1y.json"
        # Use the get_session function to create a new session object for each request
        session = get_session()
        # Use the session object to make the request
        # Use async with to ensure the session is closed properly
        # Append a random parameter to the url to bypass the cache
        # Use the headers parameter to pass a custom header
        async with session.get(url + "?rand=" + str(random.randint(0, 1000000)), headers={"Cache-Control": "no-cache"}) as response:
            # Use orjson to decode the json data
            data = json.loads(await response.read())
            # Get the Date header from the response
            date_header = response.headers['Date']
            # Parse the Date header to a datetime object
            date_header = datetime.strptime(date_header, '%a, %d %b %Y %H:%M:%S %Z')
            # Get the current time in UTC
            current_time = datetime.utcnow()
            # Calculate the difference between the current time and the Date header
            time_diff = current_time - date_header
            # Check if the response is cached or not
            # If the time difference is less than 10 seconds, assume the response is not cached
            # Otherwise, assume the response is cached
            cached = 'n' if time_diff < timedelta(seconds=10) else 'y'

        # Close the session after the request is done
        await session.close()

        # Calculate the duration of getting the json data
        network_time = round(time.perf_counter() - start_time, 2)

        # Create a dataframe from the json data
        # A dataframe is a two-dimensional data structure with rows and columns
        df = pd.DataFrame(data)

        # Convert the time column to datetime format
        # Use the pd.to_datetime() function and pass the format argument
        df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M:%S%z")

        # Set the time column as the index
        # An index is a label for each row
        df = df.set_index("time")

        # Sort the dataframe by the time index
        # Use the ascending argument to specify the order
        df = df.sort_index(ascending=True)

        # Define the end date as the most recent date in the dataframe
        # Use the max() method on the datetime column
        end_date = df.index.max()

        # Define the start dates for weekly, monthly, 6 month, and yearly timeframes
        # Use the timedelta class to subtract days from the end date
        start_date_weekly = end_date - timedelta(days=7)
        start_date_monthly = end_date - timedelta(days=30)
        start_date_6month = end_date - timedelta(days=182)
        start_date_yearly = end_date - timedelta(days=365)

        # Filter the dataframe for the defined timeframes
        # Use the loc method to select rows by index labels
        df_weekly = df.loc[start_date_weekly:end_date]
        df_monthly = df.loc[start_date_monthly:end_date]
        df_6month = df.loc[start_date_6month:end_date]
        df_yearly = df.loc[start_date_yearly:end_date]

        # Get the high and low prices for each timeframe
        # Use the max() and min() methods on the value column
        high_w = df_weekly["value"].max()
        low_w = df_weekly["value"].min()
        high_m = df_monthly["value"].max()
        low_m = df_monthly["value"].min()
        high_6m = df_6month["value"].max()
        low_6m = df_6month["value"].min()
        high_y = df_yearly["value"].max()
        low_y = df_yearly["value"].min()

        # Format the prices with commas
        # Use the f-string syntax and the comma operator
        current = f"{df.loc[end_date]['value']:,}"
        high_w = f"{high_w:,}"
        low_w = f"{low_w:,}"
        high_m = f"{high_m:,}"
        low_m = f"{low_m:,}"
        high_6m = f"{high_6m:,}"
        low_6m = f"{low_6m:,}"
        high_y = f"{high_y:,}"
        low_y = f"{low_y:,}"

        # Create a single embed object
        # An embed object is a rich message that can have fields, colors, images, etc.
        embed = discord.Embed(
            color = discord.Color.blue(),
            title = "WoW Token Price",
        )

        # Add the current price as the first field of the embed, and set inline to False
        # A field is a section of the embed that has a name and a value
        # The inline argument determines whether the field is displayed in the same line as the previous field or not
        embed.add_field(name = "Current Price", value = f"```{current} gold```", inline = False)

        # Add the rest of the pairings as fields of the embed, and set inline to True for each pair
        embed.add_field(name = "Weekly Price", value = f"```High: {high_w} gold\nLow : {low_w} gold```", inline = True)
        embed.add_field(name = "Monthly Price", value = f"```High: {high_m} gold\nLow : {low_m} gold```", inline = True)
        embed.add_field(name = "\u200b", value = "\u200b", inline = False) # blank field
        embed.add_field(name = "6 Month Price", value = f"```High: {high_6m} gold\nLow : {low_6m} gold```", inline = True)
        embed.add_field(name = "1 Year Price", value = f"```High: {high_y} gold\nLow : {low_y} gold```", inline = True)

        # Calculate the total processing time
        processing_time = round(time.perf_counter() - start_time, 2)

        # Set the footer of the embed with the metrics
        # Add the cached check to the end of the footer
        embed.set_footer(text=f"n: {network_time} | p: {processing_time} | c: {cached}")

        # Edit the loading message with the embed
        # Use the content argument to clear the text and the embed argument to add the embed
        await loading_message.edit(content=None, embed=embed)

    @commands.command()
    async def tokenalert(self, ctx, amount: str):
        """Sets an alert for the wow token price in US region"""
        # Check if the amount is a valid number
        if not amount.isdigit():
            await ctx.send("Invalid amount of gold. Please enter a positive integer.")
            return

        # Convert the amount to an integer
        threshold = int(amount)

        # Create a new task for the user
        task = loop.create_task(send_alert(ctx.author, threshold))

        # Store the task in the dictionary
        self.tasks[ctx.author.id] = task

        # Send a confirmation message
        await ctx.send(f"Alert set. You will receive a DM when the wow token price is lower than or equal to {threshold:,} gold.")

    async def send_alert(self, user, threshold):
    """Sends a DM to the user with the current wow token price if it is lower than or equal to the threshold"""
    # Get the current time in UTC
    now = datetime.utcnow()

    # Calculate the next 5 PM in UTC
    next_5pm = now.replace(hour=17, minute=0, second=0, microsecond=0)
    if now.hour >= 17:
        # Add one day to the next 5 PM
        next_5pm += timedelta(days=1)

    # Calculate the seconds to wait
    delta = next_5pm - now
    seconds = delta.total_seconds()

    # Wait until 5 PM
    await asyncio.sleep(seconds)

    # Loop indefinitely
    while True:
        # Get the json data from the url
        url = "https://data.wowtoken.app/token/history/us/1y.json"
        # Use the get_session function to create a new session object for each request
        session = get_session()
        # Use the session object to make the request
        # Use async with to ensure the session is closed properly
        # Append a random parameter to the url to bypass the cache
        # Use the headers parameter to pass a custom header
        async with session.get(url + "?rand=" + str(random.randint(0, 1000000)), headers={"Cache-Control": "no-cache"}) as response:
            # Use orjson to decode the json data
            data = json.loads(await response.read())

        # Close the session after the request is done
        await session.close()

        # Create a dataframe from the json data
        df = pd.DataFrame(data)

        # Convert the time column to datetime format
        df["time"] = pd.to_datetime(df["time"], format="%Y-%m-%dT%H:%M:%S%z")

        # Set the time column as the index
        df = df.set_index("time")

        # Sort the dataframe by the time index
        df = df.sort_index(ascending=True)

        # Define the end date as the most recent date in the dataframe
        end_date = df.index.max()

        # Get the current price
        current = df.loc[end_date]["value"]

        # Format the price with commas
        current = f"{current:,}"

        # Check if the current price is lower than or equal to the threshold
        if current <= threshold:
            # Create a single embed object
            embed = discord.Embed(
                color = discord.Color.blue(),
                title = "WoW Token Price Alert",
            )

            # Add the current price as the first field of the embed, and set inline to False
            embed.add_field(name = "Current Price", value = f"```{current} gold```", inline = False)

            # Set the footer of the embed with the source
            embed.set_footer(text="Data from https://wowtoken.app")

            # Send the embed to the user
            await user.send(embed=embed)

        # Wait for 24 hours
        await asyncio.sleep(86400)
