# Import the google-generativeai package
import google.generativeai as genai
# Import the discord and redbot.core packages
import discord
from redbot.core import commands

# Define a cog class that inherits from commands.Cog
class TestCog(commands.Cog):
  # Initialize the cog with the bot and the optional api key
  def __init__(self, bot, api_key=None):
    self.bot = bot
    # Set the api key attribute of the cog
    self.api_key = api_key
    # Try to configure the genai package with the api key
    try:
      genai.configure(api_key=api_key)
      # Create a generative model object for the gemini-pro model
      self.model = genai.GenerativeModel('gemini-pro')
      # Start a chat session with the model
      self.chat = self.model.start_chat(prompt=[])
    except Exception as e:
      # If the api key is not set or invalid, print the error and set the model and chat to None
      print(f'Error: {e}')
      self.model = None
      self.chat = None
    # Create a list to store the conversation history for the server or the group
    self.conversation_history = []

  # Define a command that sets the api key
  @commands.command()
  async def geminiapi(self, ctx, api_key):
    # Set the api key attribute of the cog
    self.api_key = api_key
    # Try to configure the genai package with the api key
    try:
      genai.configure(api_key=api_key)
      # Create a generative model object for the gemini-pro model
      self.model = genai.GenerativeModel('gemini-pro')
      # Start a chat session with the model
      self.chat = self.model.start_chat(prompt=[])
      # Send a confirmation message to the user
      await ctx.send(f'Gemini API key set to {api_key}')
    except Exception as e:
      # If the api key is invalid, send an error message to the user
      await ctx.send(f'Invalid API key: {e}')

  # Define a listener that responds to bot mentions
  @commands.Cog.listener()
  async def on_message(self, message):
    # Check if the message mentions the bot
    if self.bot.user in message.mentions:
      # Check if the model and chat are not None
      if self.model is not None and self.chat is not None:
        # Append the message content to the conversation history
        self.conversation_history.append(message.content)
        # Generate a response from the model using the send_message method, passing the message content and the stream parameter as True
        response = self.chat.send_message(content=message.content, stream=True)
        # Send the response to the user
        for chunk in response:
          await message.channel.send(chunk.text)
          # Append the response text to the conversation history
          self.conversation_history.append(chunk.text)
      else:
        # If the model or chat is None, send a message to the user to set the api key first
        await message.channel.send('Please set the Gemini API key first using the geminiapi command.')