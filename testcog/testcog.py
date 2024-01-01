# Import the google-generativeai package
import google.generativeai as genai

# Define a cog class that inherits from commands.Cog
class GeminiCog(commands.Cog):
  # Initialize the cog with the bot and the api key
  def __init__(self, bot, api_key):
    self.bot = bot
    # Configure the genai package with the api key
    genai.configure(api_key=api_key)
    # Create a generative model object for the gemini-pro model
    self.model = genai.GenerativeModel('gemini-pro')

  # Define a command that sets the api key
  @commands.command()
  async def geminiapi(self, ctx, api_key):
    # Set the api key attribute of the cog
    self.api_key = api_key
    # Configure the genai package with the api key
    genai.configure(api_key=api_key)
    # Send a confirmation message to the user
    await ctx.send(f'Gemini API key set to {api_key}')

  # Define a listener that responds to bot mentions
  @commands.Cog.listener()
  async def on_message(self, message):
    # Check if the message mentions the bot
    if self.bot.user in message.mentions:
      # Generate a response using the gemini model
      response = self.model.generate_content(message.content)
      # Send the response to the user
      await message.channel.send(response.text)