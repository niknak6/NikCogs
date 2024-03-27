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
        pokemon = await self.client.get_pokemon(pokemon_number)
        # Create the embed
        embed = discord.Embed(title="A wild Pokémon has appeared!", color=discord.Color.green())
        embed.set_thumbnail(url=pokemon.sprites.front_default)
        # Send the embed
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(PokemonSpawn(bot))