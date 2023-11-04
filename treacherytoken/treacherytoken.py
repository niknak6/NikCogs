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
        change = data["us"]["last_change"] # This is the line that passes the integer as a raw number
        one_day_low = data["us"]["1_day_low"]
        one_day_high = data["us"]["1_day_high"]
        seven_day_low = data["us"]["7_day_low"]
        seven_day_high = data["us"]["7_day_high"]
        thirty_day_low = data["us"]["30_day_low"]
        thirty_day_high = data["us"]["30_day_high"]

        # Convert the values to integers
        price = int(price)
        change = int(change)
        one_day_low = int(one_day_low)
        one_day_high = int(one_day_high)
        seven_day_low = int(seven_day_low)
        seven_day_high = int(seven_day_high)
        thirty_day_low = int(thirty_day_low)
        thirty_day_high = int(thirty_day_high)

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
        change_emoji = "📈" if change > 0 else "📉" # This is the emoji for the last change
        embed.add_field(name="", value=f"Current Price: {price} ({change_emoji} {change})") # This is the merged field with the emoji
        embed.add_field(name="", value=f"Updated {timestamp}") # This is the field without the small text
        embed.add_field(name="", value="\n", inline=False) # This is the line break using the newline character
        one_day_low_emoji = "📈" if price > one_day_low else "📉" # This is the emoji for the 1 day low
        embed.add_field(name="", value=f"1 Day Low {one_day_low_emoji}: {one_day_low} ({price - one_day_low})", inline=True) # This is the field with the emoji and the difference
        one_day_high_emoji = "📈" if price < one_day_high else "📉" # This is the emoji for the 1 day high
        embed.add_field(name="", value=f"1 Day High {one_day_high_emoji}: {one_day_high} ({one_day_high - price})", inline=True) # This is the field with the emoji and the difference
        embed.add_field(name="", value="\n", inline=False) # This is the line break using the newline character
        seven_day_low_emoji = "📈" if price > seven_day_low else "📉" # This is the emoji for the 7 day low
        embed.add_field(name="", value=f"7 Day Low {seven_day_low_emoji}: {seven_day_low} ({price - seven_day_low})", inline=True) # This is the field with the emoji and the difference
        seven_day_high_emoji = "📈" if price < seven_day_high else "📉" # This is the emoji for the 7 day high
        embed.add_field(name="", value=f"7 Day High {seven_day_high_emoji}: {seven_day_high} ({seven_day_high - price})", inline=True) # This is the field with the emoji and the difference
        embed.add_field(name="", value="\n", inline=False) # This is the line break using the newline character
        thirty_day_low_emoji = "📈" if price > thirty_day_low else "📉" # This is the emoji for the 30 day low
        embed.add_field(name="", value=f"30 Day Low {thirty_day_low_emoji}: {thirty_day_low} ({price - thirty_day_low})", inline=True) # This is the field with the emoji and the difference
        thirty_day_high_emoji = "📈" if price < thirty_day_high else "📉" # This is the emoji for the 30 day high
        embed.add_field(name="", value=f"30 Day High {thirty_day_high_emoji}: {thirty_day_high} ({thirty_day_high - price})", inline=True) # This is the field with the emoji and the difference

        # Send the embed message
        await ctx.send(embed=embed)
