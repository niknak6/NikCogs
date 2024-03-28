from redbot.core import commands
import pokebase as pb
import discord
import random

class TreacheryPokemonV2(commands.Cog):
    """TreacheryPokemonV2 - A Redbot cog to spawn Pokemon images."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def v2spawn(self, ctx):
        """Spawns a random Pokemon image."""
        # Get a random pokemon number
        pokemon_number = random.randint(1, pb.APIResourceList('pokemon').count)
        # Fetch the official artwork using the SpriteResource
        sprite_resource = pb.SpriteResource('pokemon', pokemon_number, other=True, official_artwork=True)
        artwork_url = sprite_resource.url
        # Create an embed with the Pokemon image
        embed = discord.Embed(title="A wild Pokémon appeared!")
        embed.set_image(url=artwork_url)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(TreacheryPokemonV2(bot))