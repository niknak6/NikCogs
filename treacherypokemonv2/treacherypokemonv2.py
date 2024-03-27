from redbot.core import commands
import discord
import pokepy
import random

class TreacheryPokemonV2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.client = pokepy.V2Client()

    @commands.command()
    async def v2spawn(self, ctx):
        # Generate a random pokemon number between 1 and 1025
        pokemon_number = random.randint(1, 1025)
        # Fetch the pokemon
        pokemon_list = self.client.get_pokemon(pokemon_number)
        # Assuming the first pokemon in the list is the one you want
        pokemon = pokemon_list[0] if pokemon_list else None
        if pokemon:
            # Output the list of all attributes of the sprites object
            attributes = dir(pokemon.sprites)
            await ctx.send(f"Attributes of the sprites object: {attributes}")
        else:
            await ctx.send("No Pokémon found.")

def setup(bot):
    bot.add_cog(TreacheryPokemonV2(bot))