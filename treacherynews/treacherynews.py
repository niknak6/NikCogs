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

        # Define the image size, box size, and margin
        image_width, image_height = 600, 300
        box_width, box_height = (image_width - 3 * 20) // 2, (image_height - 100 - 3 * 20) // 2
        margin = 20

        # Create a blank image with a transparent background
        image = Image.new("RGBA", (image_width, image_height))

        # Create a draw object
        draw = ImageDraw.Draw(image)

        # Load the default font
        font = ImageFont.load_default()

        # Draw the headline with a larger font and centered alignment
        draw.text((image_width // 2, 30), "Treachery News", fill="hotpink", font=font, anchor="mm")

        # Draw a horizontal line below the headline
        draw.line((0, 60, image_width, 60), fill="hotpink", width=2)  # Increased the line width

        # Define the text for each box
        texts = ["Article 1: Lorem ipsum dolor sit amet, consectetur adipiscing elit.", 
                 "Article 2: Sed quis nisi quis augue gravida fermentum.", 
                 "Article 3: Quisque euismod leo at nisl ullamcorper, ac aliquet erat lacinia.",
                 "Article 4: Fusce vitae nisi quis eros tincidunt consequat."]

        # Draw a 2x2 grid of boxes for the articles with margins and draw the text in each box
        for i in range(2):
            for j in range(2):
                # Calculate the position of the box
                left = margin + (box_width + margin) * i
                top = 80 + (box_height + margin) * j  # Added the extra space to the top margin
                right = left + box_width
                bottom = top + box_height

                # Draw the box
                draw.rectangle((left, top, right, bottom), outline="hotpink", width=2)  # Increased the line width

                # Get the text for the box
                text = texts[i * 2 + j]

                # Wrap the text into lines that fit within the box
                lines = textwrap.wrap(text, width=40)

                # Draw the text in the box
                x = left + box_width // 2
                y = top + margin
                for line in lines:
                    draw.text((x, y), line, fill="hotpink", font=font, align="center", anchor="ma")  # Changed the text color to hot pink
                    y += font.getbbox(line)[3] + 10  # Increase the y coordinate by the height of the line and some spacing

        # Save the image
        image.save("news.png")

        # Send the image to the channel
        await ctx.send(file=discord.File("news.png"))