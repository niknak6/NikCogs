# Import ast library
import ast

# Import BeautifulSoup, json, and re libraries
from bs4 import BeautifulSoup
import json
import re

# Import requests library
import requests

# Import commands module from redbot.core
from redbot.core import commands

# Define a class named TreacheryTimers that inherits from commands.Cog
class TreacheryTimers(commands.Cog):
    """A cog that shows the raid reset days for WoW Season of Discovery"""

    # Define an __init__ method that takes a bot parameter and assigns it to self.bot
    def __init__(self, bot):
        self.bot = bot

    # Define a commands.command decorator that defines a command named timers
    @commands.command()
    async def timers(self, ctx):
        """Shows the raid reset days for WoW Season of Discovery"""
        # Get the html content of the website and assign it to html
        html = requests.get('https://classicraidreset.com').content

        # Decode the bytes object to a string
        html = html.decode('utf-8')

        # Parse the html source code of the website using BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Find the wire:snapshot element and get the events attribute as a Python object
        snapshot = soup.find('div', attrs={'wire:snapshot': True})
        events = ast.literal_eval(snapshot['wire:snapshot']) # Use the ast.literal_eval function to evaluate the string as a Python object

        # Convert the Python object to a valid JSON string
        events = json.dumps(events)

        # Load the JSON string as a Python dictionary and get the data property, which contains the events array
        events = json.loads(events)
        events = events['data']['s'] # Access the events array by the 's' key

        # Filter the events by the type property, which should be instance
        events = [event for event in events if event['type'] == 'instance']

        # Format the start and title properties of each event as a string, separated by a space, and join them with newlines
        output = '\n'.join([f"{event['start']} {event['title']}" for event in events])

        # Send the formatted string to the channel where the command was used, using ctx.send
        await ctx.send(output)