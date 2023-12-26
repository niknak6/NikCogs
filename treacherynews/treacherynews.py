# Import the required modules
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFont
import discord # Import the discord module
import textwrap # Import the textwrap module

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

        # Define the text for the left box
        text = "Article 1: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Article 2: Sed quis nisi quis augue gravida fermentum. Article 3: Quisque euismod leo at nisl ullamcorper, ac aliquet erat lacinia."

        # Wrap the text into lines that fit within the box
        lines = textwrap.wrap(text, width=40)

        # Define the margins and the spacing
        margin = 10
        spacing = 10

        # Draw the lines with a smaller font and center alignment
        x = 200 # Use the center of the box as the x coordinate
        y = 150 + margin
        for line in lines:
            draw.text((x, y), line, fill=(0, 0, 0), font=font, align="center", anchor="ma") # Use the align argument to center the text horizontally and the anchor argument to center the text vertically
            y += font.getbbox(line)[3] + spacing # Increase the y coordinate by the bottom coordinate of the bounding box and the spacing

        # Draw a box for the articles on the right side of the image
        draw.rectangle((450, 150, 750, 450), fill=(255, 255, 255), outline=(0, 0, 0))

        # Define the text for the right box
        text = "Article 4: Fusce vitae nisi quis eros tincidunt consequat. Article 5: Morbi id magna vitae nunc sagittis tristique. Article 6: Praesent vel neque quis elit faucibus blandit."

        # Wrap the text into lines that fit within the box
        lines = textwrap.wrap(text, width=40)

        # Define the margins and the spacing
        margin = 10
        spacing = 10

        # Draw the lines with a smaller font and center alignment
        x = 600 # Use the center of the box as the x coordinate
        y = 150 + margin
        for line in lines:
            draw.text((x, y), line, fill=(0, 0, 0), font=font, align="center", anchor="ma") # Use the align argument to center the text horizontally and the anchor argument to center the text vertically
            y += font.getbbox(line)[3] + spacing # Increase the y coordinate by the bottom coordinate of the bounding box and the spacing

        # Draw a box for the New York Times logo on the top left corner of the image
        draw.rectangle((50, 10, 150, 90), fill=(255, 255, 255), outline=(0, 0, 0))

        # Draw a box for the photo related to the first article on the right side of the image
        draw.rectangle((450, 10, 750, 90), fill=(255, 255, 255), outline=(0, 0, 0))

        # Save the image
        image.save("news.png")

        # Send the image to the channel
        await ctx.send(file=discord.File("news.png"))