from redbot.core import commands
import requests
import pandas as pd
import discord
from datetime import datetime, timedelta # CHANGE: added timedelta

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

        # Create a dataframe from the json data
        df = pd.DataFrame(data)

        # Convert the time column to datetime format
        df["time"] = pd.to_datetime(df["time"])

        # Set the time column as the index
        df = df.set_index("time")

        # Define the end date as the most recent date in the dataframe
        end_date = df.index.max()

        # Define the start dates for weekly, monthly, 6 month, and yearly timeframes
        start_date_weekly = end_date - timedelta(days=7) # CHANGE: subtract 7 days from end date
        start_date_monthly = end_date - timedelta(days=30) # CHANGE: subtract 30 days from end date
        start_date_6month = end_date - timedelta(days=182) # CHANGE: subtract 182 days from end date
        start_date_yearly = end_date - timedelta(days=365) # CHANGE: subtract 365 days from end date

        # Filter the dataframe for the defined timeframes
        df_weekly = df.loc[start_date_weekly:end_date] # CHANGE: use start_date_weekly as lower bound
        df_monthly = df.loc[start_date_monthly:end_date] # CHANGE: use start_date_monthly as lower bound
        df_6month = df.loc[start_date_6month:end_date] # CHANGE: use start_date_6month as lower bound
        df_yearly = df.loc[start_date_yearly:end_date] # CHANGE: use start_date_yearly as lower bound

        # Get the high and low prices for each timeframe
        high_w = df_weekly["value"].max()
        low_w = df_weekly["value"].min()
        high_m = df_monthly["value"].max()
        low_m = df_monthly["value"].min()
        high_6m = df_6month["value"].max() # CHANGE: get the 6 month high price
        low_6m = df_6month["value"].min() # CHANGE: get the 6 month low price
        high_y = df_yearly["value"].max()
        low_y = df_yearly["value"].min()

        # Format the prices with commas
        current = f"{df.iloc[-1]['value']:,}"
        high_w = f"{high_w:,}"
        low_w = f"{low_w:,}"
        high_m = f"{high_m:,}"
        low_m = f"{low_m:,}"
        high_6m = f"{high_6m:,}" # CHANGE: format the 6 month high price
        low_6m = f"{low_6m:,}" # CHANGE: format the 6 month low price
        high_y = f"{high_y:,}"
        low_y = f"{low_y:,}"

        # Create a single embed object
        embed = discord.Embed(
            color = discord.Color.blue(), # set the color of the embed
            title = "WoW Token Price", # set the title of the embed
        )

        # Set the timestamp of the embed with the timestamp attribute
        embed.timestamp = datetime.now() # use the current time as the timestamp

        # Add the current price as the first field of the embed, and set inline to False
        embed.add_field(name = "Current Price", value = f"```{current} gold```", inline = False)

        # Add the rest of the pairings as fields of the embed, and set inline to True for each pair
        embed.add_field(name = "Weekly Price", value = f"```High: {high_w} gold\nLow : {low_w} gold```", inline = True)
        embed.add_field(name = "Monthly Price", value = f"```High: {high_m} gold\nLow : {low_m} gold```", inline = True)
        embed.add_field(name = "\u200b", value = "\u200b", inline = False) # blank field
        embed.add_field(name = "6 Month Price", value = f"```High: {high_6m} gold\nLow : {low_6m} gold```", inline = True) # CHANGE: add the 6 month price field
        embed.add_field(name = "1 Year Price", value = f"```High: {high_y} gold\nLow : {low_y} gold```", inline = True)

        # Send the embed message with the send method
        await ctx.send(embed=embed) # send the embed as the message