# Import the required modules
from bs4 import BeautifulSoup
import requests
from redbot.core import commands
from datetime import datetime
import pytz
import re # Import the re module
import json # Import the json module

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
            import re
            sections = soup.find_all("section", id=re.compile("^US-group-raidresets"))

            # Check if the sections are not empty
            if sections:
                # Initialize an empty list to store the timers and names
                mylist = [" ".join(div.get_text() for div in section.find_all("div", class_="tiw-line")) for section in sections]

                # Zip the list into pairs of name and timer
                pairs = zip(mylist[::2], mylist[1::2])

                # Send the timers and names to the user
                await ctx.send("Here are the raid reset timers for classic wow (Eastern Time):")
                # Use a formatted string to display the pairs
                await ctx.send("\n".join(f"**{name}**: {timer}" for name, timer in pairs))
            else:
                # Handle the case when the sections are empty
                # Define a variable that stores the url of the js file
                js_url = "https://wow.zamimg.com/widgets/power.js"
                # Make a request to the js url and get the response content
                js_response = requests.get(js_url)
                js_content = js_response.text
                # Parse the js content and extract the array of objects that contains the raid reset timers
                pattern = r"WH\.Wow\.TodayInWow\(\w+, (\[.*?\])\)"
                match = re.search(pattern, js_content)
                # Check if the match is not None
                if match is None:
                    # Handle the case when the js content does not have the raid reset timers
                    await ctx.send("Sorry, I could not find the raid reset timers in the js file.")
                else:
                    # Get the array of objects from the match group and convert it to a Python list or dictionary
                    js_data = json.loads(match.group(1))
                    # Access the raid reset timers for the US region and group by indexing the list or dictionary
                    us_timers = [group for group in js_data if group["regionId"] == "US"]
                    # Send the raid reset timers to the user
                    await ctx.send("Here are the raid reset timers for classic wow (Eastern Time):")
                    # Use a formatted string to display the pairs
                    await ctx.send("\n".join(f"**{line['name']}**: {line['endingShort']}" for group in us_timers for line in group["content"]["lines"].values()))

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
