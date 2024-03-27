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
                # Create the embed
                embed = discord.Embed(title="A wild Pokémon has appeared!", color=discord.Color.green())
                embed.set_thumbnail(url=pokemon.sprites.front_default)
                # Send the embed
                await ctx.send(embed=embed)
            else:
                await ctx.send("No Pokémon found.")

def setup(bot):
    bot.add_cog(PokemonSpawn(bot))