from redbot.core import commands
import requests
import random
import discord

class TreacheryPokemon(commands.Cog):
    """A cog for spawning and catching Pokémon with treachery."""

    def __init__(self, bot):
        self.bot = bot
        self.current_pokemon = None
        self.current_sprite = None

    @commands.command()
    async def spawn(self, ctx):
        """Spawns a random Pokémon."""
        pokemon_id = random.randint(1, 898)  # There are 898 Pokémon as of Generation VIII
        response = requests.get(f'https://pokeapi.co/api/v2/pokemon/{pokemon_id}')
        if response.ok:
            pokemon_data = response.json()
            self.current_pokemon = pokemon_data['name']
            self.current_sprite = pokemon_data['official-artwork']['front_default']
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

def setup(bot):
    bot.add_cog(TreacheryPokemon(bot))