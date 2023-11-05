from redbot.core import commands
import requests
import pandas as pd
import discord # import the discord library
from datetime import datetime # import the datetime class from the datetime module

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

        # Create a single embed object
        embed = discord.Embed(
            color = discord.Color.blue(), # set the color of the embed
            title = "Wow Token Price", # set the title of the embed
        )

        # Set the author of the embed with the set_author method
        embed.set_author(name = "TreacheryToken", icon_url = self.bot.user.avatar.url) # use the bot's name and avatar as the author

        # Set the timestamp of the embed with the timestamp attribute
        embed.timestamp = datetime.now() # use the current time as the timestamp

        # Add the current price as the first field of the embed, and set inline to False
        embed.add_field(name = "Current Price", value = f"{current} gold", inline = False)

        # Add the rest of the pairings as fields of the embed, and set inline to True for each pair
        embed.add_field(name = "Weekly High Price", value = f"{high_w} gold", inline = True)
        embed.add_field(name = "Weekly Low Price", value = f"{low_w} gold", inline = True)
        embed.add_field(name = "Monthly High Price", value = f"{high_m} gold", inline = True)
        embed.add_field(name = "Monthly Low Price", value = f"{low_m} gold", inline = True)
        embed.add_field(name = "6 Month High Price", value = f"{high_6m} gold", inline = True)
        embed.add_field(name = "6 Month Low Price", value = f"{low_6m} gold", inline = True)
        embed.add_field(name = "1 Year High Price", value = f"{high_y} gold", inline = True)
        embed.add_field(name = "1 Year Low Price", value = f"{low_y} gold", inline = True)

        # Send the embed message with the send method
        await ctx.send(embed = embed) # send the embed as the message
