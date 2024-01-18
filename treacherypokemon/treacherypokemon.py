from redbot.core import commands, config
from redbot.core.commands import CaseInsensitiveLiteral # Import the converter
import requests
import random
import discord

class TreacheryPokemon(commands.Cog):
    """A cog for spawning and catching Pokémon with treachery."""

    def __init__(self, bot):
        self.bot = bot
        self.current_pokemon = None
        self.current_sprite = None
        # Create a Config object for this cog
        self.config = config.Config.get_conf(self, identifier=1234567890)
        # Register a user setting for storing the starter Pokémon
        self.config.register_user(starter=None)

    @commands.command()
    async def spawn(self, ctx):
        """Spawns a random Pokémon."""
        pokemon_id = random.randint(1, 898)  # There are 898 Pokémon as of Generation VIII
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}')
        if response.ok:
            pokemon_data = response.json()
            self.current_pokemon = pokemon_data['name']
            self.current_sprite = pokemon_data['sprites']['other']['official-artwork']['front_default']
            embed = discord.Embed(title=f"A wild {self.current_pokemon.capitalize()} has appeared!")
            embed.set_image(url=self.current_sprite)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Failed to spawn a Pokémon. Please try again.")

    @commands.command(name="pokecatch")
    async def pokecatch(self, ctx):
        """Catches the current Pokémon."""
        if self.current_pokemon:
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            self.current_pokemon = None
            self.current_sprite = None
        else:
            await ctx.send("There's no Pokémon to catch. Use the `spawn` command to spawn one.")

    @commands.command(name="choosestarter")
    async def choosestarter(self, ctx, pokemon: CaseInsensitiveLiteral(*starters) = None): # Use the converter and pass the list of starters
        """Picks a starter Pokémon from a list of options."""
        # Get the user ID of the command author
        user_id = ctx.author.id
        # Get the starter Pokémon stored for this user, if any
        starter = await self.config.user(ctx.author).starter()
        # If the user already has a starter, inform them and return
        if starter is not None:
            await ctx.send(f"You already have a starter Pokémon: {starter.capitalize()}.")
            return
        # Otherwise, create a dictionary of starter Pokémon options by generation
        starters = {
            1: ["Bulbasaur", "Charmander", "Squirtle", "Pikachu", "Eevee"],
            2: ["Chikorita", "Cyndaquil", "Totodile"],
            3: ["Treecko", "Torchic", "Mudkip"],
            4: ["Turtwig", "Chimchar", "Piplup"],
            5: ["Snivy", "Tepig", "Oshawott"],
            6: ["Chespin", "Fennekin", "Froakie"],
            7: ["Rowlet", "Litten", "Popplio"],
            8: ["Grookey", "Scorbunny", "Sobble"]
        }
        # If the user did not provide an argument, send a message with the list of options and a reminder
        if pokemon is None:
            message = "Please pick a starter Pokémon from the following options:\n"
            # Loop through the dictionary keys and values
            for generation, pokemon in starters.items():
                message += f"Generation {generation}: "
                message += ", ".join(pokemon) + "\n"
            message += "Use the command `!choosestarter` followed by the name of your choice."
            await ctx.send(message)
            return
        # If the user provided an argument, check if it is a valid choice
        if pokemon.lower() in [p for v in starters.values() for p in v]:
            # Store the starter Pokémon for this user in the config
            await self.config.user(ctx.author).starter.set(pokemon.lower())
            # Inform the user of their choice
            await ctx.send(f"You picked {pokemon.capitalize()} as your starter Pokémon!")
        else:
            # If the argument is not a valid choice, inform the user and return
            await ctx.send(f"{pokemon} is not a valid starter Pokémon. Please choose from the list of options.")
            return

def setup(bot):
    bot.add_cog(TreacheryPokemon(bot))