# Import the required modules
from redbot.core import commands
from PIL import Image, ImageDraw, ImageFont
import discord
import textwrap

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
        image = Image.new("RGB", (900, 900), (240, 240, 240))  # Increased the size of the image

        # Create a draw object
        draw = ImageDraw.Draw(image)

        # Load the default font
        font = ImageFont.load_default()

        # Draw a horizontal line below the headline
        draw.line((0, 100, 900, 100), fill=(0, 0, 0))

        # Draw the headline with a larger font and centered alignment
        draw.text((450, 50), "Treachery News", fill=(0, 0, 0), font=font, anchor="mm")

        # Define the margins and the spacing
        margin = 10
        spacing = 10

        # Draw a 2x2 grid of boxes for the articles with margins
        box_margin = 50  # Define the margin between boxes
        for i in range(2):
            for j in range(2):
                draw.rectangle((50 + 450 * i + box_margin * i, 150 + 375 * j + box_margin * j, 350 + 450 * i + box_margin * i, 525 + 375 * j + box_margin * j), fill=(255, 255, 255), outline=(0, 0, 0))  # Adjusted the box size and position

        # Define the text for each box
        texts = ["Article 1: Lorem ipsum dolor sit amet, consectetur adipiscing elit.", 
                 "Article 2: Sed quis nisi quis augue gravida fermentum.", 
                 "Article 3: Quisque euismod leo at nisl ullamcorper, ac aliquet erat lacinia.",
                 "Article 4: Fusce vitae nisi quis eros tincidunt consequat."]

        # Draw the text in each box
        for i in range(2):
            for j in range(2):
                text = texts[i * 2 + j]
                lines = textwrap.wrap(text, width=40)
                x = 200 + 450 * i + box_margin * i  # Adjusted the text position
                y = 150 + 375 * j + margin + box_margin * j  # Adjusted the text position
                for line in lines:
                    draw.text((x, y), line, fill=(0, 0, 0), font=font, align="center", anchor="ma")
                    y += font.getbbox(line)[3] + spacing

        # Save the image
        image.save("news.png")

        # Send the image to the channel
        await ctx.send(file=discord.File("news.png"))