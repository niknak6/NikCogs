from redbot.core import commands
import requests
import pandas as pd

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

        # Get the current price from the last entry
        current = df.iloc[-1]["value"]

        # Resample the dataframe to find the high and low prices for each period
        # W = weekly, M = monthly, 6M = 6 month, Y = year
        # max and min are the aggregation functions to find the high and low prices
        resampled = df.resample("W").agg({"value": ["max", "min"]}) # Resample by week
        high_w = resampled.iloc[-1]["value"]["max"] # Get the weekly high price
        low_w = resampled.iloc[-1]["value"]["min"] # Get the weekly low price
        resampled = df.resample("M").agg({"value": ["max", "min"]}) # Resample by month
        high_m = resampled.iloc[-1]["value"]["max"] # Get the monthly high price
        low_m = resampled.iloc[-1]["value"]["min"] # Get the monthly low price
        resampled = df.resample("6M").agg({"value": ["max", "min"]}) # Resample by 6 month
        high_6m = resampled.iloc[-1]["value"]["max"] # Get the 6 month high price
        low_6m = resampled.iloc[-1]["value"]["min"] # Get the 6 month low price
        resampled = df.resample("Y").agg({"value": ["max", "min"]}) # Resample by year
        high_y = resampled.iloc[-1]["value"]["max"] # Get the 1 year high price
        low_y = resampled.iloc[-1]["value"]["min"] # Get the 1 year low price

        # Format the prices with commas
        current = f"{current:,}"
        high_w = f"{high_w:,}"
        low_w = f"{low_w:,}"
        high_m = f"{high_m:,}"
        low_m = f"{low_m:,}"
        high_6m = f"{high_6m:,}"
        low_6m = f"{low_6m:,}"
        high_y = f"{high_y:,}"
        low_y = f"{low_y:,}"

        # Send the message with the prices
        await ctx.send(f"The current price of the wow token is {current}.\nThe weekly high price is {high_w} and the weekly low price is {low_w}.\nThe monthly high price is {high_m} and the monthly low price is {low_m}.\nThe 6 month high price is {high_6m} and the 6 month low price is {low_6m}.\nThe 1 year high price is {high_y} and the 1 year low price is {low_y}.")
