# Import the required modules
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFont
import discord # Import the discord module

# Define the cog class
class TreacheryNews(commands.Cog):
    """A cog that generates a newspaper image"""

    def __init__(self, bot):
        self.bot = bot

    # Define the news command
    @commands.command()
    async def news(self, ctx):
        """Generate a newspaper image"""

        # Create a blank image with a light gray background
        image = Image.new("RGB", (800, 600), (240, 240, 240))

        # Create a draw object
        draw = ImageDraw.Draw(image)

        # Load the default font
        font = ImageFont.load_default()

        # Draw a horizontal line below the headline
        draw.line((0, 100, 800, 100), fill=(0, 0, 0))

        # Draw a vertical line between the articles
        draw.line((400, 150, 400, 600), fill=(0, 0, 0))

        # Draw the headline with a larger font and centered alignment
        draw.text((400, 50), "Treachery News", fill=(0, 0, 0), font=font, anchor="mm") # Use the anchor argument to center the text

        # Draw a box for the articles on the left side of the image
        draw.rectangle((50, 150, 350, 450), fill=(255, 255, 255), outline=(0, 0, 0))

        # Draw the articles with a smaller font and left alignment
        draw.text((50, 150), "Article 1: Lorem ipsum dolor sit amet, consectetur adipiscing elit.", fill=(0, 0, 0), font=font, anchor="la") # Use the anchor argument to align the text to the left
        draw.text((50, 200), "Article 2: Sed quis nisi quis augue gravida fermentum.", fill=(0, 0, 0), font=font, anchor="la")
        draw.text((50, 250), "Article 3: Quisque euismod leo at nisl ullamcorper, ac aliquet erat lacinia.", fill=(0, 0, 0), font=font, anchor="la")

        # Draw a box for the New York Times logo on the top left corner of the image
        draw.rectangle((50, 10, 150, 90), fill=(255, 255, 255), outline=(0, 0, 0))

        # Draw a box for the photo related to the first article on the right side of the image
        draw.rectangle((450, 150, 750, 450), fill=(255, 255, 255), outline=(0, 0, 0))

        # Save the image
        image.save("news.png")

        # Send the image to the channel
        await ctx.send(file=discord.File("news.png"))