# Import the required modules
from redbot.core import commands
import requests
import pandas as pd
import discord
from datetime import datetime, timedelta
from natsort import index_natsorted # CHANGE: import the natsort module

class TreacheryToken(commands.Cog):
    """A cog that shows the price of the wow token"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the current, weekly, monthly, 6 month and 1 year high and low price of the wow token in US region"""
        # Get the json data from the url
        url = "https://data.wowtoken.app/token/history/us/1y.json"
        response = requests.get(url)
        data = response.json()

        # Check if the web request was successful
        if response.status_code == 200: # CHANGE: add an if statement to check the status code
            # Create a dataframe from the json data and flatten it
            df = pd.json_normalize(data, record_path='data') # CHANGE: use 'data' instead of 'content' as the record_path

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

            # Filter the dataframe for the defined timeframes
            df_weekly = df.loc[start_date_weekly:end_date]
            df_monthly = df.loc[start_date_monthly:end_date]
            df_6month = df.loc[start_date_6month:end_date]
            df_yearly = df.loc[start_date_yearly:end_date]

            # Get the high and low prices for each timeframe
            high_w = df_weekly["value"].max()
            low_w = df_weekly["value"].min()
            high_m = df_monthly["value"].max()
            low_m = df_monthly["value"].min()
            high_6m = df_6month["value"].max()
            low_6m = df_6month["value"].min()
            high_y = df_yearly["value"].max()
            low_y = df_yearly["value"].min()

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

            # Create a single embed object
            embed = discord.Embed(
                color = discord.Color.blue(),
                title = "WoW Token Price",
            )

            # Set the timestamp of the embed with the current time
            embed.timestamp = datetime.now()

            # Add the current price as the first field of the embed, and set inline to False
            embed.add_field(name = "Current Price", value = f"```{current} gold```", inline = False)

            # Add the rest of the pairings as fields of the embed, and set inline to True for each pair
            embed.add_field(name = "Weekly Price", value = f"```High: {high_w} gold\nLow : {low_w} gold```", inline = True)
            embed.add_field(name = "Monthly Price", value = f"```High: {high_m} gold\nLow : {low_m} gold```", inline = True)
            embed.add_field(name = "\u200b", value = "\u200b", inline = False) # blank field
            embed.add_field(name = "6 Month Price", value = f"```High: {high_6m} gold\nLow : {low_6m} gold```", inline = True)
            embed.add_field(name = "1 Year Price", value = f"```High: {high_y} gold\nLow : {low_y} gold```", inline = True)

            # Send the embed message with the send method
            await ctx.send(embed=embed)
        else: # CHANGE: add an else statement to handle the error
            # Send an error message with the status code
            await ctx.send(f"Sorry, something went wrong. The web request returned a status code of {response.status_code}.")
