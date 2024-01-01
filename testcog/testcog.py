# Import the google-generativeai package
import google.generativeai as genai
# Import the commands module from redbot.core
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
    except Exception as e:
      # If the api key is not set or invalid, print the error and set the model to None
      print(f'Error: {e}')
      self.model = None

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
      # Check if the model is not None
      if self.model is not None:
        # Generate a response using the gemini model
        response = self.model.generate_content(message.content)
        # Send the response to the user
        await message.channel.send(response.text)
      else:
        # If the model is None, send a message to the user to set the api key first
        await message.channel.send('Please set the Gemini API key first using the geminiapi command.')