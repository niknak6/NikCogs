from redbot.core import commands
from selenium import webdriver
from bs4 import BeautifulSoup

class TreacheryTimers(commands.Cog):
    """A cog that shows raid reset timers from https://classicraidreset.com/US/SoD"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def timers(self, ctx):
        """This shows the raid reset timers from the website."""

        # Start a new Chrome session
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")  # Run Chrome in headless mode (without opening GUI)
        driver = webdriver.Chrome(options=options)

        # Define the URL
        URL = "https://classicraidreset.com/US/SoD"

        try:
            # Open the URL
            driver.get(URL)

            # Wait for the page to load (you might need to adjust this delay)
            driver.implicitly_wait(10)

            # Get the page source
            page_source = driver.page_source

            # Use BeautifulSoup to parse the page source
            soup = BeautifulSoup(page_source, "html.parser")

            # Find the div element that contains the calendar data
            calendar = soup.find("div", id="calendar-element")

            # Find the script element inside the calendar div that has a wire:snapshot attribute
            script = calendar.find("script", attrs={"wire:snapshot": True})

            # Get the value of the wire:snapshot attribute as a string
            snapshot = script["wire:snapshot"]

            # Process the snapshot as needed (remaining code similar to your original approach)
            data = json.loads(snapshot)
            events = data["data"]["events"]
            event_list = []

            for event in events:
                event_list.append(format_event(event))

            event_str = "\n".join(event_list)
            await ctx.send(event_str)

        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

        finally:
            # Close the browser session after scraping
            driver.quit()