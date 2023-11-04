# Import the necessary modules
import discord
from redbot.core import commands
import requests

# Define the cog class
class TreacheryToken(commands.Cog):
    """A cog that shows the WoW token price"""

    def __init__(self, bot):
        self.bot = bot

    # Define the command
    @commands.command()
    async def wowtoken(self, ctx):
        """Shows the WoW token price in US region"""

        # Get the json data from the website
        url = "https://wowtokenprices.com/current_prices.json"
        response = requests.get(url)
        data = response.json()

        # Extract the relevant information
        price = data["us"]["current_price"]
        time = data["us"]["time_of_last_change_unix_epoch"]
        change = data["us"]["last_change"]
        one_day_low = data["us"]["1_day_low"]
        one_day_high = data["us"]["1_day_high"]
        seven_day_low = data["us"]["7_day_low"]
        seven_day_high = data["us"]["7_day_high"]
        thirty_day_low = data["us"]["30_day_low"]
        thirty_day_high = data["us"]["30_day_high"]

        # Format the values with commas
        price = f"{price:,}"
        change = "{:+,}".format(change)
        one_day_low = f"{one_day_low:,}"
        one_day_high = f"{one_day_high:,}"
        seven_day_low = f"{seven_day_low:,}"
        seven_day_high = f"{seven_day_high:,}"
        thirty_day_low = f"{thirty_day_low:,}"
        thirty_day_high = f"{thirty_day_high:,}"

        # Create the dynamic timestamp syntax
        timestamp = f"<t:{time}:f>"

        # Create the embed message
        embed = discord.Embed(title=":coin: WoW Token Price :coin:", color=0x00ff00)
        embed.add_field(name="", value=f"Current Price 📈 {price}")
        embed.add_field(name="", value=f"Last Change {change}")
        embed.add_field(name="", value=f"Updated {timestamp}")
        embed.add_field(name="", value="\u200b", inline=False) # This is the line break using the zero-width space character
        embed.add_field(name="", value=f"1 Day Low 📉 {one_day_low}", inline=True) # This is the field without the bullet point
        embed.add_field(name="", value=f"1 Day High 📈 {one_day_high}", inline=True) # This is the field without the bullet point
        embed.add_field(name="", value="\u200b", inline=False) # This is the line break using the zero-width space character
        embed.add_field(name="", value=f"7 Day Low 📉 {seven_day_low}", inline=True) # This is the field without the bullet point
        embed.add_field(name="", value=f"7 Day High 📈 {seven_day_high}", inline=True) # This is the field without the bullet point
        embed.add_field(name="", value="\u200b", inline=False) # This is the line break using the zero-width space character
        embed.add_field(name="", value=f"30 Day Low 📉 {thirty_day_low}", inline=True) # This is the field without the bullet point
        embed.add_field(name="", value=f"30 Day High 📈 {thirty_day_high}", inline=True) # This is the field without the bullet point

        # Send the embed message
        await ctx.send(embed=embed)
