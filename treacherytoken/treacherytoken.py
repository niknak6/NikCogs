# Import the time module
import time

# Import the other modules
from redbot.core import commands
import requests
import pandas as pd
import discord
from datetime import datetime, timedelta

# Import orjson as json
import orjson as json

# Import requests-cache
import requests_cache

class TreacheryToken(commands.Cog):
    """A cog that shows the price of the wow token"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the current, weekly, monthly, 6 month and 1 year high and low price of the wow token in US region"""
        # Use the global variable render_time
        global render_time

        # Get the start time of the whole code
        start_time = time.time()

        # Get the json data from the url
        url = "https://data.wowtoken.app/token/history/us/1y.json"
        # Use the requests-cache context manager to disable caching
        with requests_cache.disabled():
            # Use requests to make the request
            response = requests.get(url)
        # Use orjson to decode the json data
        data = json.loads(response.content)

        # Get the end time of getting the json data
        end_time = time.time()

        # Calculate the duration of getting the json data
        network_time = round(end_time - start_time, 2)

        # Get the start time of creating the dataframe
        start_time = time.time()

        # Create a dataframe from the json data
        df = pd.DataFrame(data)

        # Convert the time column to datetime format
        df["time"] = pd.to_datetime(df["time"])

        # Set the time column as the index
        df = df.set_index("time")

        # Define the end date as the most recent date in the dataframe
        end_date = df.index.max()

        # Define the start dates for weekly, monthly, 6 month, and yearly timeframes
        start_date_weekly = end_date - timedelta(days=7)
        start_date_monthly = end_date - timedelta(days=30)
        start_date_6month = end_date - timedelta(days=182)
        start_date_yearly = end_date - timedelta(days=365)

        # Get the end time of creating the dataframe
        end_time = time.time()

        # Calculate the duration of creating the dataframe
        dataframe_time = round(end_time - start_time, 2)

        # Get the start time of filtering the data
        start_time = time.time()

        # Filter the dataframe for the defined timeframes
        df_weekly = df.loc[start_date_weekly:end_date]
        df_monthly = df.loc[start_date_monthly:end_date]
        df_6month = df.loc[start_date_6month:end_date]
        df_yearly = df.loc[start_date_yearly:end_date]

        # Get the end time of filtering the data
        end_time = time.time()

        # Calculate the duration of filtering the data
        filter_time = round(end_time - start_time, 2)

        # Get the start time of getting the high and low prices
        start_time = time.time()

        # Get the high and low prices for each timeframe
        high_w = df_weekly["value"].max()
        low_w = df_weekly["value"].min()
        high_m = df_monthly["value"].max()
        low_m = df_monthly["value"].min()
        high_6m = df_6month["value"].max()
        low_6m = df_6month["value"].min()
        high_y = df_yearly["value"].max()
        low_y = df_yearly["value"].min()

        # Get the end time of getting the high and low prices
        end_time = time.time()

        # Calculate the duration of getting the high and low prices
        price_time = round(end_time - start_time, 2)

        # Get the start time of formatting the prices
        start_time = time.time()

        # Format the prices with commas
        current = f"{df.iloc[-1]['value']:,}"
        high_w = f"{high_w:,}"
        low_w = f"{low_w:,}"
        high_m = f"{high_m:,}"
        low_m = f"{low_m:,}"
        high_6m = f"{high_6m:,}"
        low_6m = f"{low_6m:,}"
        high_y = f"{high_y:,}"
        low_y = f"{low_y:,}"

        # Get the end time of formatting the prices
        end_time = time.time()

        # Calculate the duration of formatting the prices
        format_time = round(end_time - start_time, 2)

        # Calculate the total processing time
        processing_time = round(dataframe_time + filter_time + price_time + format_time, 2)

        # Create a single embed object
        embed = discord.Embed(
            color = discord.Color.blue(),
            title = "WoW Token Price",
        )

        # Set the timestamp of the embed with the timestamp attribute
        embed.timestamp = datetime.now()

        # Add the current price as the first field of the embed, and set inline to False
        embed.add_field(name = "Current Price", value = f"```{current} gold```", inline = False)

        # Add the rest of the pairings as fields of the embed, and set inline to True for each pair
        embed.add_field(name = "Weekly Price", value = f"```High: {high_w} gold\nLow : {low_w} gold```", inline = True)
        embed.add_field(name = "Monthly Price", value = f"```High: {high_m} gold\nLow : {low_m} gold```", inline = True)
        embed.add_field(name = "\u200b", value = "\u200b", inline = False) # blank field
        embed.add_field(name = "6 Month Price", value = f"```High: {high_6m} gold\nLow : {low_6m} gold```", inline = True)
        embed.add_field(name = "1 Year Price", value = f"```High: {high_y} gold\nLow : {low_y} gold```", inline = True)

        # Set the footer of the embed with the metrics
        embed.set_footer(text=f"n: {network_time} | p: {processing_time}")

        # Send the embed message with the send method
        await ctx.send(embed=embed)
