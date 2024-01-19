# Import the required modules
from redbot.core import commands, Config
import aiohttp
import random
import discord
# Import the BotEmbedPaginator class from Simple Embed Pagination
from simple_embed_pagination import BotEmbedPaginator

class TreacheryPokemon(commands.Cog):
    """A cog for spawning and catching Pokémon with pokeapi.co"""

    def __init__(self, bot):
        self.bot = bot
        self.current_pokemon = None
        self.current_sprite = None
        self.base_url = "https://pokeapi.co/api/v2/" # The base URL of the pokeapi.co
        self.max_pokemon = 1025 # The maximum number of Pokémon as of Generation VIII
        # Create a Config object to store the cog settings
        self.config = Config.get_conf(self, identifier=1234567890)
        # Register the default settings
        default_guild = {
            "spawn_channel": None, # The channel where Pokémon will spawn
            "spawn_chance": 0.1, # The probability of a Pokémon spawning after a message
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
    async def spawn(self, ctx):
        """Spawns a random Pokémon."""
        # Get the spawn channel ID from the config
        spawn_channel = await self.config.guild(ctx.guild).spawn_channel()
        # If the context channel is the same as the spawn channel
        if ctx.channel.id == spawn_channel:
            # Generate a random Pokémon ID
            pokemon_id = random.randint(1, self.max_pokemon)
            # Construct the URL of the Pokémon API endpoint
            pokemon_url = self.base_url + f"pokemon/{pokemon_id}"
            # Create an aiohttp session
            async with aiohttp.ClientSession() as session:
                # Make a GET request to the Pokémon API endpoint
                async with session.get(pokemon_url) as response:
                    # If the response status is OK
                    if response.status == 200:
                        # Parse the JSON data from the response
                        pokemon_data = await response.json()
                        # Get the name and sprite of the Pokémon
                        self.current_pokemon = pokemon_data['name']
                        # Change this line to use the official artwork image
                        self.current_sprite = pokemon_data['sprites']['other']['official-artwork']['front_default']
                        # Create an embed to display the Pokémon
                        embed = discord.Embed(title=f"A wild {self.current_pokemon.capitalize()} has appeared!")
                        embed.set_image(url=self.current_sprite)
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
        # Get the spawn channel ID from the config
        spawn_channel = await self.config.guild(message.guild).spawn_channel()
        # If the message is in the spawn channel
        if message.channel.id == spawn_channel:
            # Get the spawn chance from the config
            spawn_chance = await self.config.guild(message.guild).spawn_chance()
            # Generate a random number between 0 and 1
            rand = random.random()
            # If the random number is less than the spawn chance
            if rand < spawn_chance:
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
            # If the Pokémon is already in the pokedex
            if self.current_pokemon in pokedex:
                # Increment the count of the Pokémon by 1
                pokedex[self.current_pokemon] += 1
            # Otherwise
            else:
                # Set the count of the Pokémon to 1
                pokedex[self.current_pokemon] = 1
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
            # Create a constant variable for the number of pokemon per page
            POKEMON_PER_PAGE = 10
            # Create a list of embeds to paginate
            embeds = []
            # For each Pokémon and its count in the pokedex
            for pokemon_name, pokemon_count in pokedex.items():
                # Get the sprite URL of the Pokémon from the pokeapi.co
                pokemon_url = self.base_url + f"pokemon/{pokemon_name}"
                # Create an aiohttp session
                async with aiohttp.ClientSession() as session:
                    # Make a GET request to the Pokémon API endpoint
                    async with session.get(pokemon_url) as response:
                        # If the response status is OK
                        if response.status == 200:
                            # Parse the JSON data from the response
                            pokemon_data = await response.json()
                            # Get the sprite URL of the Pokémon
                            pokemon_sprite = pokemon_data['sprites']['other']['official-artwork']['front_default']
                        # Otherwise
                        else:
                            # Use a default sprite URL
                            pokemon_sprite = "https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/0.png"
                # Create an embed with the Pokémon name, sprite and count
                embed = discord.Embed(
                    title=f"{ctx.author.name}'s Pokedex",
                    color=discord.Color.red()
                )
                embed.add_field(name=pokemon_name, value=f"{pokemon_sprite} x{pokemon_count}", inline=True)
                # If the embed has reached the maximum number of fields per page
                if len(embed.fields) == POKEMON_PER_PAGE:
                    # Add the embed to the list of embeds
                    embeds.append(embed)
                    # Create a new embed for the next page
                    embed = discord.Embed(
                        title=f"{ctx.author.name}'s Pokedex",
                        color=discord.Color.red()
                    )
            # If the embed still has some fields left
            if embed.fields:
                # Add the embed to the list of embeds
                embeds.append(embed)
            # Create a BotEmbedPaginator object with the left and right arrow emojis
            bot_paginator = BotEmbedPaginator(ctx, embeds, left="◀️", right="▶️")
            # Run the paginator
            await bot_paginator.start()
        # Otherwise
        else:
            # Send a message that the pokedex is empty
            await ctx.send("You have not caught any Pokémon yet.")

def setup(bot):
    bot.add_cog(TreacheryPokemon(bot))