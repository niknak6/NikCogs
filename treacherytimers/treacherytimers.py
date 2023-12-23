# Import lxml.html and json libraries
import lxml.html
import json

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
        # Change the URL to the one you specified
        html = requests.get('https://classicraidreset.com/US/SoD').content

        # Parse the html source code of the website using lxml.html
        tree = lxml.html.fromstring(html)

        # Find the wire:snapshot element and get the events attribute as a JSON string
        snapshot = tree.xpath('//div[@wire:snapshot]/@wire:snapshot')[0]

        # Load the JSON string as a Python dictionary and get the data property, which contains the events array
        events = json.loads(snapshot)
        events = events['data']['s'] # Access the events array by the 's' key

        # Filter the events by the type property, which should be instance
        events = [event for event in events if event['type'] == 'instance']

        # Format the start and title properties of each event as a string, separated by a space, and join them with newlines
        output = '\n'.join([f"{event['start']} {event['title']}" for event in events])

        # Send the formatted string to the channel where the command was used, using ctx.send
        await ctx.send(output)