# Import the commands and utils modules from the redbot.core packages
from redbot.core import commands, utils

# Import the requests and beautifulsoup4 libraries
import requests
from bs4 import BeautifulSoup

# Define a constant for the website URL
URL = "https://classicraidreset.com/US/SoD"

# Define a helper function to format the event data as a string
def format_event(event):
    # Get the event id, title, start date, and end date
    event_id = event["id"]
    event_title = event["title"]
    event_start = event["start"]
    event_end = event["end"]

    # Return a formatted string with the event details
    return f"**{event_title}**\nID: {event_id}\nStart: {event_start}\nEnd: {event_end}\n"

# Define a cog class that inherits from commands.Cog
class TreacheryTimers(commands.Cog):
    """A cog that shows raid reset timers from https://classicraidreset.com/US/SoD"""

    # Define the constructor method
    def __init__(self, bot):
        # Assign the bot instance to an attribute
        self.bot = bot

    # Define a command method with the name timers
    @commands.command()
    async def timers(self, ctx):
        """This shows the raid reset timers from the website."""

        # Send a GET request to the website and get the response
        response = requests.get(URL)

        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            # Parse the response content as HTML using beautifulsoup4
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the div element that contains the calendar data
            calendar = soup.find("div", id="calendar-element")

            # Find the script element inside the calendar div that has a wire:snapshot attribute
            script = calendar.find("script", attrs={"wire:snapshot": True})

            # Get the value of the wire:snapshot attribute as a string
            snapshot = script["wire:snapshot"]

            # Parse the snapshot string as a JSON object
            data = utils.chat_formatting.escape(json.loads(snapshot), mass_mentions=True)

            # Get the events array from the data object
            events = data["data"]["events"]

            # Initialize an empty list to store the formatted events
            event_list = []

            # Loop through the events array
            for event in events:
                # Format the event data as a string and append it to the event list
                event_list.append(format_event(event))

            # Join the event list with newlines and assign it to a variable
            event_str = "\n".join(event_list)

            # Send the event string as a message to the context channel
            await ctx.send(event_str)
        else:
            # Send an error message to the context channel
            await ctx.send("Sorry, something went wrong. Please try again later.")