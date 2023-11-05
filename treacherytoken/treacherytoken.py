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

        # Create an array of embed objects
        embeds = []

        # Create an embed object for the current price
        current_embed = discord.Embed(
            color = discord.Color.blue(), # set the color of the embed
            title = "Current Price", # set the title of the embed
            description = f"The current price of the wow token in US region is {current} gold." # set the description of the embed
        )

        # Set the author of the embed with the set_author method
        current_embed.set_author(name = "TreacheryToken", icon_url = self.bot.user.avatar.url) # use the bot's name and avatar as the author

        # Set the timestamp of the embed with the timestamp attribute
        current_embed.timestamp = datetime.now() # use the current time as the timestamp

        # Append the current embed to the embeds array
        embeds.append(current_embed)

        # Create an embed object for the weekly price
        weekly_embed = discord.Embed(
            color = discord.Color.blue(), # set the color of the embed
            title = "Weekly Price", # set the title of the embed
        )

        # Add fields to the embed with the add_field method
        weekly_embed.add_field(name = "High Price", value = f"{high_w} gold", inline = True) # add the weekly high price field and set inline to True
        weekly_embed.add_field(name = "Low Price", value = f"{low_w} gold", inline = True) # add the weekly low price field and set inline to True

        # Set the author of the embed with the set_author method
        weekly_embed.set_author(name = "TreacheryToken", icon_url = self.bot.user.avatar.url) # use the bot's name and avatar as the author

        # Set the timestamp of the embed with the timestamp attribute
        weekly_embed.timestamp = datetime.now() # use the current time as the timestamp

        # Append the weekly embed to the embeds array
        embeds.append(weekly_embed)

        # Create an embed object for the monthly price
        monthly_embed = discord.Embed(
            color = discord.Color.blue(), # set the color of the embed
            title = "Monthly Price", # set the title of the embed
        )

        # Add fields to the embed with the add_field method
        monthly_embed.add_field(name = "High Price", value = f"{high_m} gold", inline = True) # add the monthly high price field and set inline to True
        monthly_embed.add_field(name = "Low Price", value = f"{low_m} gold", inline = True) # add the monthly low price field and set inline to True

        # Set the author of the embed with the set_author method
        monthly_embed.set_author(name = "TreacheryToken", icon_url = self.bot.user.avatar.url) # use the bot's name and avatar as the author

        # Set the timestamp of the embed with the timestamp attribute
        monthly_embed.timestamp = datetime.now() # use the current time as the timestamp

        # Append the monthly embed to the embeds array
        embeds.append(monthly_embed)

        # Create an embed object for the 6 month price
        six_month_embed = discord.Embed(
            color = discord.Color.blue(), # set the color of the embed
            title = "6 Month Price", # set the title of the embed
        )

        # Add fields to the embed with the add_field method
        six_month_embed.add_field(name = "High Price", value = f"{high_6m} gold", inline = True) # add the 6 month high price field and set inline to True
        six_month_embed.add_field(name = "Low Price", value = f"{low_6m} gold", inline = True) # add the 6 month low price field and set inline to True

        # Set the author of the embed with the set_author method
        six_month_embed.set_author(name = "TreacheryToken", icon_url = self.bot.user.avatar.url) # use the bot's name and avatar as the author

        # Set the timestamp of the embed with the timestamp attribute
        six_month_embed.timestamp = datetime.now() # use the current time as the timestamp

        # Append the 6 month embed to the embeds array
        embeds.append(six_month_embed)

        # Create an embed object for the 1 year price
        one_year_embed = discord.Embed(
            color = discord.Color.blue(), # set the color of the embed
            title = "1 Year Price", # set the title of the embed
        )

        # Add fields to the embed with the add_field method
        one_year_embed.add_field(name = "High Price", value = f"{high_y} gold", inline = True) # add the 1 year high price field and set inline to True
        one_year_embed.add_field(name = "Low Price", value = f"{low_y} gold", inline = True) # add the 1 year low price field and set inline to True

        # Set the author of the embed with the set_author method
        one_year_embed.set_author(name = "TreacheryToken", icon_url = self.bot.user.avatar.url) # use the bot's name and avatar as the author

        # Set the timestamp of the embed with the timestamp attribute
        one_year_embed.timestamp = datetime.now() # use the current time as the timestamp

        # Append the 1 year embed to the embeds array
        embeds.append(one_year_embed)

        # Send the embed message with the send method
        await ctx.send(embeds = embeds) # send the embeds array as the message
