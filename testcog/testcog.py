# Import the commands module from redbot.core
from redbot.core import commands

# Import the requests module to make HTTP requests to the gemini-pro API
import requests

# Define a constant for the gemini-pro API endpoint
GEMINI_PRO_API = "https://api.gemini-pro.google.com/v1/generate"

# Define a constant for your gemini-pro API key
# Note: You should keep your API key secret and not share it with anyone
GEMINI_PRO_KEY = "AIzaSyCaa3qXhCKf_8gffMFus0winnucnl_KMyk"

# Create a class that inherits from commands.Cog
class TestCog(commands.Cog):
    """A cog that interacts with gemini-pro"""

    # Define the __init__ method that takes the bot instance as an argument
    def __init__(self, bot):
        # Assign the bot instance to self.bot
        self.bot = bot

    # Define a command decorator that takes the name of the command as an argument
    @commands.command(name="test")
    # Define the command method that takes the context as an argument
    async def test_command(self, ctx):
        """Generate a response from gemini-pro"""

        # Get the message content from the context
        message = ctx.message.content

        # Check if the message mentions the bot
        if self.bot.user.mentioned_in(ctx.message):
            # Remove the bot mention from the message
            message = message.replace(f"<@!{self.bot.user.id}>", "")

            # Create a payload dictionary with the message as the input
            payload = {"input": message}

            # Create a headers dictionary with the API key as the authorization
            headers = {"Authorization": f"Bearer {GEMINI_PRO_KEY}"}

            # Make a POST request to the gemini-pro API with the payload and headers
            response = requests.post(GEMINI_PRO_API, json=payload, headers=headers)

            # Check if the request was successful
            if response.status_code == 200:
                # Get the output from the response JSON
                output = response.json().get("output")

                # Send the output as a reply to the message
                await ctx.reply(output)
            else:
                # Send an error message
                await ctx.reply("Sorry, something went wrong. Please try again later.")