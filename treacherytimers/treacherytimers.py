# Import the required modules
from bs4 import BeautifulSoup
import requests
from redbot.core import commands
from datetime import datetime
import pytz

# Define the cog class
class TreacheryTimers(commands.Cog):
    """A cog that parses raid reset timers from wowhead.com/classic"""

    def __init__(self, bot):
        self.bot = bot
        # Define a variable to control debug dumping
        self.debug = False

    @commands.command()
    async def timers(self, ctx):
        """Shows the raid reset timers for classic wow"""

        # Define the url and the headers
        url = "https://www.wowhead.com/classic"
        headers = {"User-Agent": "Red-DiscordBot/3.5"}

        # Make a request and get the response
        response = requests.get(url, headers=headers)

        # Check if the response is successful
        if response.status_code == 200:
            # Parse the response content with beautifulsoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find all the sections with the raid reset timers
            sections = soup.find_all("section", id="US-group-raidresets")

            # Check if the sections are not empty
            if sections:
                # Initialize an empty list to store the timers and names
                timers_and_names = []

                # Loop through the sections
                for section in sections:
                    # Find all the direct children of the section that are tags
                    children = section.find_all(recursive=False)

                    # Loop through the children
                    for child in children:
                        # Check if the child is a section element
                        if child.name == "section":
                            # Try to get the timer as a timestamp
                            try:
                                timer = child["data-ut"]
                            except KeyError:
                                # Handle the error if the attribute is not found
                                # For example, skip the element or log the error message
                                continue

                            # Convert the timestamp to an integer
                            timer = int(timer)

                            # Convert the timestamp to a datetime object
                            timer = datetime.fromtimestamp(timer)

                            # Convert the datetime object to eastern time
                            utc = pytz.utc
                            eastern = pytz.timezone("US/Eastern")
                            timer = utc.localize(timer).astimezone(eastern)

                            # Format the datetime object as a string
                            timer = timer.strftime("%Y-%m-%d %H:%M:%S")

                            # Append the timer to the list
                            timers_and_names.append(timer)
                        # Check if the child is a link element
                        elif child.name == "a":
                            # Get the name of the raid
                            name = child.get_text()

                            # Append the name to the list
                            timers_and_names.append(name)

                # Send the timers and names to the user
                await ctx.send("Here are the raid reset timers for classic wow (Eastern Time):")
                # Use a code block to format the output
                await ctx.send("```")
                # Loop through the list in pairs
                for i in range(0, len(timers_and_names), 2):
                    # Get the timer and the name
                    timer = timers_and_names[i]
                    name = timers_and_names[i+1]
                    # Send the timer and the name
                    await ctx.send(f"{name}: {timer}")
                # End the code block
                await ctx.send("```")
            else:
                # Handle the case when the sections are empty
                await ctx.send("Sorry, I could not find any sections with the raid reset timers.")

        else:
            # Send an error message if the response is not successful
            await ctx.send(f"Sorry, I could not get the data from the remote host. The status code is {response.status_code}.")

        # Check if debug dumping is enabled
        if self.debug:
            # Output the response content for debugging
            await ctx.send("Here is the response content:")
            content = soup.prettify()
            # Split the content into chunks of 2000 characters
            chunks = [content[i:i+2000] for i in range(0, len(content), 2000)]
            # Send each chunk as a separate message
            for chunk in chunks:
                await ctx.send(chunk)
