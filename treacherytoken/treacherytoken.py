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
        embed.add_field(name="Current Price", value=f"📈 {price}\n")
        embed.add_field(name="Last Change", value=f"{change}\n")
        embed.add_field(name="Updated", value=timestamp)
        embed.add_field(name="", value="", inline=True) # This is the blank field to create a line break
        embed.add_field(name=" • 1 Day Low", value=f"📉 {one_day_low}", inline=True) # This is the field with a space before the bullet point
        embed.add_field(name=" • 1 Day High", value=f"📈 {one_day_high}", inline=True) # This is the field with a space before the bullet point
        # embed.add_field(name="", value="", inline=True) # This is the blank field to create a line break
        embed.add_field(name="• 7 Day Low", value=f"📉 {seven_day_low}", inline=True)
        embed.add_field(name="• 7 Day High", value=f"📈 {seven_day_high}", inline=True)
        embed.add_field(name="", value="", inline=True) # This is the blank field to create a line break
        embed.add_field(name="", value="", inline=True) # This is the blank field to create a line break
        embed.add_field(name="• 30 Day Low", value=f"📉 {thirty_day_low}", inline=True)
        embed.add_field(name="• 30 Day High", value=f"📈 {thirty_day_high}", inline=True)

        # Send the embed message
        await ctx.send(embed=embed)
