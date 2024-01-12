# Import the required modules
import os
from redbot.core import commands
from sydney import SydneyClient

# Define the cog class
class Copilot(commands.Cog):
    """A cog that allows you to chat with Copilot."""

    def __init__(self, bot):
        self.bot = bot
        self.sydney = None # The Sydney client instance
        self.channel_id = None # The channel id where the conversation is happening

    # Define a command to start a conversation with Copilot
    @commands.command()
    async def start(self, ctx):
        """Start a conversation with Copilot."""
        # Check if there is already a conversation
        if self.sydney is not None:
            await ctx.send("You are already in a conversation with Copilot.")
            return
        # Create a new Sydney client with the desired style
        self.sydney = SydneyClient(style="creative")
        # Start the conversation
        await self.sydney.start_conversation()
        # Store the channel id as an attribute
        self.channel_id = ctx.channel.id # Add this line here
        # Send a welcome message
        await ctx.send("You have started a conversation with Copilot. Type your messages here or use !copilotstop to end the conversation.")

    # Define a command to stop a conversation with Copilot
    @commands.command(name="copilotstop") # Change the command name here
    async def copilotstop(self, ctx): # Change the function name here
        """Stop a conversation with Copilot."""
        # Check if there is a conversation
        if self.sydney is None:
            await ctx.send("You are not in a conversation with Copilot.")
            return
        # Close the conversation
        await self.sydney.close_conversation()
        # Delete the Sydney client instance
        self.sydney = None
        # Send a farewell message
        await ctx.send("You have ended the conversation with Copilot. Thank you for chatting.")

    # Define a listener for messages in the same channel as the command
    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignore messages from bots
        if message.author.bot:
            return
        # Ignore messages that are not commands
        if message.content.startswith("!"):
            return
        # Check if there is a conversation
        if self.sydney is None:
            return
        # Check if the message is in the same channel as the command
        if message.channel.id != self.channel_id: # Use the message channel id here
            return
        # Get the message content
        prompt = message.content
        # Send the prompt to Copilot and stream the response
        async for response in self.sydney.ask_stream(prompt):
            await message.channel.send(response)

    # Define a command that allows the bot owner to set the cookie for Sydney.py
    @commands.command()
    @commands.is_owner() # This will make the command only available to the bot owner
    async def copilotapi(self, ctx, cookie: str):
        """Set the cookie for Sydney.py."""
        # Set the cookie as an environment variable
        os.environ["BING_COOKIES"] = cookie
        # Send a confirmation message
        await ctx.send("The cookie for Sydney.py has been set successfully.")