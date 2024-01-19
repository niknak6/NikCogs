# Import the required modules
from redbot.core import commands, Config
import requests
import random
import discord
from discord.ext import menus

class TreacheryPokemon(commands.Cog):
    """A cog for spawning and catching Pokémon with pokeapi.co"""

    def __init__(self, bot):
        self.bot = bot
        self.current_pokemon = None
        self.current_sprite = None
        self.base_url = "https://pokeapi.co/api/v2/" # The base URL of the pokeapi.co
        self.pokemon_list = None # The list of available Pokémon
        # Create a Config object to store the cog settings
        self.config = Config.get_conf(self, identifier=1234567890)
        # Register the default settings
        default_guild = {
            "spawn_channel": None, # The channel where Pokémon will spawn
        }
        default_member = {
            "pokedex": {}, # The dictionary of caught Pokémon and their counts
        }
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)

    # Define a command to set the spawn channel
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setpokemonspawn(self, ctx, channel: commands.TextChannelConverter):
        """Set the channel where Pokémon will spawn"""
        # Save the channel ID in the config
        await self.config.guild(ctx.guild).spawn_channel.set(channel.id)
        # Send a confirmation message
        await ctx.send(f"Pokémon will now spawn in {channel.mention}")

    # Define a command to spawn a Pokémon
    @commands.command()
    @commands.is_owner() # Only allow the bot owner to use this command
    @commands.cooldown(1, 60, commands.BucketType.channel) # Limit the command to once per minute per channel
    async def spawn(self, ctx):
        """Spawns a random Pokémon."""
        # Get the spawn channel from the guild
        spawn_channel = discord.utils.get(ctx.guild.channels, id=await self.config.guild(ctx.guild).spawn_channel())
        # If the context channel is the same as the spawn channel
        if ctx.channel == spawn_channel:
            # If the Pokémon list is None
            if self.pokemon_list is None:
                # Make a GET request to the Pokémon API endpoint
                response = requests.get(self.base_url + "pokemon")
                # If the response status is OK
                if response.status_code == 200:
                    # Parse the JSON data from the response
                    pokemon_data = response.json()
                    # Get the list of Pokémon results
                    self.pokemon_list = pokemon_data['results']
                # Otherwise
                else:
                    # Send an error message
                    await ctx.send("Failed to get the list of Pokémon. Please try again.")
                    # Return from the function
                    return
            # Select a random Pokémon from the list
            pokemon = random.choice(self.pokemon_list)
            # Get the name and URL of the Pokémon
            self.current_pokemon = pokemon['name']
            pokemon_url = pokemon['url']
            # Make a GET request to the Pokémon URL
            response = requests.get(pokemon_url)
            # If the response status is OK
            if response.status_code == 200:
                # Parse the JSON data from the response
                pokemon_data = response.json()
                # Get the sprite of the Pokémon
                self.current_sprite = pokemon_data['sprites']['other']['official-artwork']['front_default']
                # Create a dictionary for the embed
                embed_dict = {
                    "title": f"A wild {self.current_pokemon.capitalize()} has appeared!",
                    "image": {"url": self.current_sprite}
                }
                # Create an embed from the dictionary
                embed = discord.Embed.from_dict(embed_dict)
                # Send the embed to the context channel
                await ctx.send(embed=embed)
            # Otherwise
            else:
                # Send an error message
                await ctx.send("Failed to spawn a Pokémon. Please try again.")
        # Otherwise
        else:
            # Send a message that the command can only be used in the spawn channel
            await ctx.send(f"This command can only be used in the spawn channel. Please use the `setpokemonspawn` command to set the spawn channel first.")

    # Define a listener for message events
    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        # Ignore messages from bots or DMs
        if message.author.bot or not message.guild:
            return
        # Get the spawn channel from the guild
        spawn_channel = discord.utils.get(message.guild.channels, id=await self.config.guild(message.guild).spawn_channel())
        # If the message is in the spawn channel
        if message.channel == spawn_channel:
            # Invoke the spawn command with the message context
            await self.bot.get_command("spawn").invoke(message)

    # Define a command to catch a Pokémon
    @commands.guild_only()
    @commands.command(name="pokecatch")
    async def pokecatch(self, ctx, *, pokemon: str):
        """Catches the current Pokémon by typing its name."""
        # If the current Pokémon is not None and matches the input name
        if self.current_pokemon and self.current_pokemon == pokemon.lower():
            # Send a success message
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            # Get the pokedex of the member from the config
            pokedex = await self.config.member(ctx.author).pokedex()
            # Increment the count of the Pokémon by 1
            pokedex[self.current_pokemon] = pokedex.get(self.current_pokemon, 0) + 1
            # Save the updated pokedex in the config
            await self.config.member(ctx.author).pokedex.set(pokedex)
            # Reset the current Pokémon and sprite to None
            self.current_pokemon = None
            self.current_sprite = None
        # Otherwise
        else:
            # Send a message that the input name is incorrect or there is no Pokémon to catch
            await ctx.send("That is not the correct Pokémon name or there is no Pokémon to catch. Use the `spawn` command to spawn one.")

    # Define a command to view the pokedex
    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        """View your caught Pokémon"""
        # Get the pokedex of the member from the config
        pokedex = await self.config.member(ctx.author).pokedex()
        # If the pokedex is not empty
        if pokedex:
            # Create a list of lines for the pokedex
            lines = []
            # For each Pokémon and its count in the pokedex
            for pokemon_name, pokemon_count in pokedex.items():
                # Get the sprite URL of the Pokémon from the pokeapi.co
                pokemon_url = self.base_url + f"pokemon/{pokemon_name}"
                # Make a GET request to the Pokémon URL
                response = requests.get(pokemon_url)
                # If the response status is OK
                if response.status_code == 200:
                    # Parse the JSON data from the response
                    pokemon_data = response.json()
                    # Get the sprite URL of the Pokémon
                    pokemon_sprite = pokemon_data['sprites']['other']['official-artwork']['front_default']
                # Otherwise
                else:
                    # Use a default sprite URL
                    pokemon_sprite = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png"
                # Append a line to the list with the Pokémon name, sprite and count
                lines.append(f"{pokemon_sprite} {pokemon_name.capitalize()} x{pokemon_count}")
            # Create a paginator object with the lines
            paginator = menus.Paginator(lines, per_page=10, prefix="", suffix="")
            # Create a menu object with the paginator
            menu = menus.MenuPages(paginator, delete_message_after=True)
            # Start the menu in the context channel
            await menu.start(ctx)
        # Otherwise
        else:
            # Send a message that the pokedex is empty
            await ctx.send("You have not caught any Pokémon yet.")

def setup(bot):
    bot.add_cog(TreacheryPokemon(bot))