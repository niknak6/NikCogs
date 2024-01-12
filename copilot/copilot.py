# Import the required modules
import json
import os
from redbot.core import commands
from re_edge_gpt import Chatbot, ConversationStyle # Import ReEdgeGPT here

# Define the cog class
class Copilot(commands.Cog):
    """A cog that allows you to chat with Copilot."""

    def __init__(self, bot):
        self.bot = bot
        self.re_edge_gpt = None # The ReEdgeGPT client instance
        self.channel_id = None # The channel id where the conversation is happening

    # Define a command to start a conversation with Copilot
    @commands.command()
    async def start(self, ctx):
        """Start a conversation with Copilot."""
        # Check if there is already a conversation
        if self.re_edge_gpt is not None:
            await ctx.send("You are already in a conversation with Copilot.")
            return
        # Create a new ReEdgeGPT client with the desired style
        self.re_edge_gpt = Chatbot(conversation_style=ConversationStyle.creative) # Use ReEdgeGPT here
        # Start the conversation
        await self.re_edge_gpt.start_conversation()
        # Store the channel id as an attribute
        self.channel_id = ctx.channel.id
        # Send a welcome message
        await ctx.send("You have started a conversation with Copilot. Type your messages here or use !copilotstop to end the conversation.")

    # Define a command to stop a conversation with Copilot
    @commands.command(name="copilotstop")
    async def copilotstop(self, ctx):
        """Stop a conversation with Copilot."""
        # Check if there is a conversation
        if self.re_edge_gpt is None:
            await ctx.send("You are not in a conversation with Copilot.")
            return
        # Close the conversation
        await self.re_edge_gpt.close_conversation()
        # Delete the ReEdgeGPT client instance
        self.re_edge_gpt = None
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
        if self.re_edge_gpt is None:
            return
        # Check if the message is in the same channel as the command
        if message.channel.id != self.channel_id:
            return
        # Get the message content
        prompt = message.content
        # Send the prompt to Copilot and get the response
        response = await self.re_edge_gpt.ask(prompt) # Use ReEdgeGPT here
        # Check if the response is None
        if response is None:
            # End the conversation
            await self.copilotstop(message)
        else:
            # Send the response
            await message.channel.send(response)

    # Define a command that allows the bot owner to set the cookie for ReEdgeGPT
    @commands.command()
    @commands.is_owner()
    async def copilotapi(self, ctx, cookie: str):
        """Set the cookie for ReEdgeGPT."""
        # Parse the cookie as a list of dicts
        cookies = json.loads(cookie)
        # Set the cookie for ReEdgeGPT
        await self.re_edge_gpt.set_cookies(cookies) # Use ReEdgeGPT here
        # Send a confirmation message
        await ctx.send("The cookie for ReEdgeGPT has been set successfully.")