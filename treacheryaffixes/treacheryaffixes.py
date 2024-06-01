# Import the required modules
from redbot.core import commands
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd

# Define the scraping function
def scrape_affixes():
    # Create a driver and open the website
    driver = webdriver.Chrome()
    driver.get("https://mythicpl.us/")

    # Locate the elements that contain the affix information
    current_affixes = driver.find_element(By.ID, "thisweekus")
    next_week_affixes = driver.find_element(By.ID, "nextweek")
    week_after_next_affixes = driver.find_element(By.ID, "weekafternext")

    # Extract the text from the elements and store them in lists
    current_affixes_list = current_affixes.text.split()
    next_week_affixes_list = next_week_affixes.text.split(", ")
    week_after_next_affixes_list = week_after_next_affixes.text.split(", ")

    # Close the driver
    driver.close()

    # Format the output as a data frame
    output = pd.DataFrame({
        "Current": current_affixes_list,
        "Next Week": next_week_affixes_list,
        "Week After Next": week_after_next_affixes_list
    })

    # Return the output as a string
    return output.to_string(index=False)

# Create a cog class that inherits from commands.Cog
class TreacheryAffixes(commands.Cog):
    """A cog that scrapes affix information from mythicpl.us"""

    # Define an __init__ method that takes the bot as an argument
    def __init__(self, bot):
        self.bot = bot

    # Create a command decorator that registers the affixes command
    @commands.command()
    async def affixes(self, ctx):
        """Scrapes and displays the affix information from mythicpl.us"""
        # Call the scraping function and store the output in a variable
        output = scrape_affixes()
        # Send the output to the context channel
        await ctx.send(output)