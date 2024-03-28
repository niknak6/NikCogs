from redbot.core import commands
import pokebase as pb, discord, random

class TreacheryPokemonV2(commands.Cog):
    def __init__(self, bot): self.bot = bot
    @commands.command()
    async def v2spawn(self, ctx):
        try:
            num = random.randint(1, 1050)
            url = pb.SpriteResource('pokemon', num, other=True, official_artwork=True).url
            await ctx.send(embed=discord.Embed(title="A wild Pokémon appeared!").set_image(url=url))
        except pb.HTTPError as e:
            await ctx.send("Sorry, no artwork found for this Pokémon." if e.response.status_code == 404 else "An error occurred while fetching the Pokémon artwork.")

def setup(bot): bot.add_cog(TreacheryPokemonV2(bot))