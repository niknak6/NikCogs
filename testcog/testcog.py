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
      self.chat = self.model.start_chat(history=[])
    except Exception as e:
      # If the api key is not set or invalid, print the error and set the model and chat to None
      print(f'Error: {e}')
      self.model = None
      self.chat = None
    # Create a dictionary to store the conversation histories for each user or channel
    self.conversation_histories = {}

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
      self.chat = self.model.start_chat(history=[])
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
        # Get the user or channel ID as the conversation ID
        conversation_id = str(message.author.id) if message.guild is None else str(message.channel.id)
        # Get the conversation history for the conversation ID, or create an empty list if it does not exist
        conversation_history = self.conversation_histories.get(conversation_id, [])
        # Generate a response using the gemini model, passing the message content, conversation ID and history as parameters
        response = self.chat.send_message(message.content, conversation_id=conversation_id, conversation_history=conversation_history, stream=True)
        # Send the response to the user
        for chunk in response:
          await message.channel.send(chunk.text)
          # Append the user's message and the bot's response to the conversation history
          conversation_history.append(glm.Content(parts=[glm.Part(text=message.content)], role="user"))
          conversation_history.append(glm.Content(parts=[glm.Part(text=chunk.text)], role="model"))
        # Update the conversation history in the dictionary
        self.conversation_histories[conversation_id] = conversation_history
      else:
        # If the model or chat is None, send a message to the user to set the api key first
        await message.channel.send('Please set the Gemini API key first using the geminiapi command.')