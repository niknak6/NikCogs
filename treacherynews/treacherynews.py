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
        image = Image.new("RGB", (800, 800), (240, 240, 240))

        # Create a draw object
        draw = ImageDraw.Draw(image)

        # Load the default font
        font = ImageFont.load_default()

        # Draw a horizontal line below the headline
        draw.line((0, 80, 800, 80), fill=(0, 0, 0))  # Moved the line up

        # Draw the headline with a larger font and centered alignment
        draw.text((400, 40), "Treachery News", fill=(0, 0, 0), font=font, anchor="mm")  # Moved the headline up

        # Define the margins and the spacing
        margin = 10
        spacing = 10

        # Draw a 2x2 grid of boxes for the articles with margins
        box_margin = 20  # Reduced the margin between boxes
        box_size = (800 - 3 * box_margin) // 2  # Adjusted the box size
        for i in range(2):
            for j in range(2):
                draw.rectangle((box_margin + (box_size + box_margin) * i, 100 + (box_size + box_margin) * j, box_margin + box_size + (box_size + box_margin) * i, 100 + box_size + (box_size + box_margin) * j), fill=(255, 255, 255), outline=(0, 0, 0))

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
                x = box_margin + box_size // 2 + (box_size + box_margin) * i  # Adjusted the text position
                y = 100 + margin + (box_size + box_margin) * j  # Adjusted the text position
                for line in lines:
                    draw.text((x, y), line, fill=(0, 0, 0), font=font, align="center", anchor="ma")
                    y += font.getbbox(line)[3] + spacing

        # Save the image
        image.save("news.png")

        # Send the image to the channel
        await ctx.send(file=discord.File("news.png"))