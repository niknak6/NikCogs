import random
import requests
from redbot.core import commands, Config
import discord
from io import BytesIO
import traceback

class TreacheryPokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_pokemon = None
        self.current_sprite = None
        self.base_url = "https://pokeapi.co/api/v2/pokemon/"
        self.pokemon_count = 1025
        self.config = Config.get_conf(self, identifier=1234567890)
        default_guild = {
            "spawn_channel": None,
            "spawn_rate": 0.0,
        }
        default_member = {
            "pokedex": {},
        }
        self.config.register_guild(**default_guild)
        self.config.register_member(**default_member)
        self.spawn_message = None

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setpokemonspawn(self, ctx, channel: commands.TextChannelConverter, spawn_rate: float):
        await self.config.guild(ctx.guild).spawn_channel.set(channel.id)
        await self.config.guild(ctx.guild).spawn_rate.set(spawn_rate / 100)
        await ctx.send(f"Pokémon will now spawn in {channel.mention} with a spawn rate of {spawn_rate}% per message.")

    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 60, commands.BucketType.channel)
    async def spawn(self, ctx):
        spawn_channel = discord.utils.get(ctx.guild.channels, id=await self.config.guild(ctx.guild).spawn_channel())
        if ctx.channel == spawn_channel:
            pokemon_id = random.randint(1, self.pokemon_count)
            pokemon_url = self.base_url + str(pokemon_id)
            response = requests.get(pokemon_url)
            if response.status_code == 200:
                pokemon_data = response.json()
                self.current_pokemon = pokemon_data['name']
                self.current_sprite = pokemon_data['sprites']['other']['official-artwork']['front_default']
                image_data = BytesIO (requests.get (self.current_sprite).content)
                image_file = discord.File (image_data, filename="pokemon.png")
                embed_dict = {
                    "title": "A wild Pokemon has appeared!",
                    "image": {"url": "attachment://pokemon.png"}
                }
                embed = discord.Embed.from_dict(embed_dict)
                self.spawn_message = await ctx.send(file=image_file, embed=embed)
            else:
                await ctx.send("Failed to spawn a Pokémon. Please try again.")
        else:
            await ctx.send(f"This command can only be used in the spawn channel. Please use the `setpokemonspawn` command to set the spawn channel first.")

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.author.bot or not message.guild:
            return
        spawn_channel = discord.utils.get(message.guild.channels, id=await self.config.guild(message.guild).spawn_channel())
        spawn_rate = await self.config.guild(message.guild).spawn_rate()
        if message.channel == spawn_channel and random.random() < spawn_rate:
            ctx = await self.bot.get_context(message)
            await self.bot.get_command("spawn").invoke(ctx)

    @commands.guild_only()
    @commands.command(name="pokecatch")
    async def pokecatch(self, ctx, *, pokemon: str):
        pokemon = pokemon.replace(" ", "-")
        if self.current_pokemon and self.current_pokemon == pokemon.lower():
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            pokedex = await self.config.member(ctx.author).pokedex()
            pokedex[self.current_pokemon] = pokedex.get(self.current_pokemon, 0) + 1
            await self.config.member(ctx.author).pokedex.set(pokedex)
            if self.spawn_message:
                new_embed = discord.Embed(title="Pokemon Caught", description=f"{self.current_pokemon.capitalize()} was caught by {ctx.author.name}.")
                await self.spawn_message.edit(embed=new_embed)
            self.current_pokemon = None
            self.current_sprite = None
            self.spawn_message = None
        else:
            await ctx.send("That is not the correct Pokémon name or there is no Pokémon to catch. Use the `spawn` command to spawn one.")

    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        pokedex = await self.config.member(ctx.author).pokedex()
        if pokedex:
            # create a list of embeds to paginate
            embeds = []
            for pokemon_name, pokemon_count in pokedex.items():
                embed = discord.Embed(title=f"{pokemon_name.capitalize()} x {pokemon_count}", color=discord.Color.random())
                embed.set_image(url=self.base_url + pokemon_name + "/")
                embeds.append(embed)
            # create a custom view for pagination
            view = PokedexView(ctx, embeds)
            # send the first embed with the view
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

# a custom view class for pagination
class PokedexView(discord.ui.View):
    def __init__(self, ctx, embeds):
        super().__init__(timeout=None) # this will make the view last indefinitely
        self.ctx = ctx # the context of the command
        self.embeds = embeds # the list of embeds to paginate
        self.current = 0 # the current page index
        self.total = len(embeds) # the total number of pages

    # a helper method to update the embed footer
    def update_footer(self):
        self.embeds[self.current].set_footer(text=f"Page {self.current + 1} of {self.total}")

    # a button for going to the previous page
    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction, button): # change the order of parameters
        # check if the user is the author of the command
        if interaction.user == self.ctx.author:
            # decrement the current page index
            self.current -= 1
            # wrap around if it goes below zero
            if self.current < 0:
                self.current = self.total - 1
            # update the embed footer
            self.update_footer()
            # edit the message with the new embed
            try:
                await interaction.message.edit(embed=self.embeds[self.current])
            except Exception as e:
                print(e) # print the exception to the console
        else:
            # send an error message if the user is not the author
            try:
                await interaction.response.send_message("Only the author of the command can use this button.", ephemeral=True)
            except Exception as e:
                print(e) # print the exception to the console

    # a button for going to the next page
    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction, button): # change the order of parameters
        # check if the user is the author of the command
        if interaction.user == self.ctx.author:
            # increment the current page index
            self.current += 1
            # wrap around if it goes above the total
            if self.current >= self.total:
                self.current = 0
            # update the embed footer
            self.update_footer()
            # edit the message with the new embed
            try:
                await interaction.message.edit(embed=self.embeds[self.current])
            except Exception as e:
                print(e) # print the exception to the console
        else:
            # send an error message if the user is not the author
            try:
                await interaction.response.send_message("Only the author of the command can use this button.", ephemeral=True)
            except Exception as e:
                print(e) # print the exception to the console

# define the on_interaction event
@bot.event
async def on_interaction(interaction):
    # check if the interaction is a button click
    if interaction.type == discord.InteractionType.component:
        # get the view from the message
        view = interaction.message.view
        # process the interaction with the view
        await view.process_interaction(interaction)

def setup(bot):
    bot.add_cog(TreacheryPokemon(bot))