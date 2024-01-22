import discord
from discord.ext import commands
from discord.ext.commands import Bot
import asyncio
import json
import os
import random
import requests
import logging
import sqlite3
import secrets
from io import BytesIO

logger = logging.getLogger("red.treacherypokemon")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename="treacherypokemon.log", encoding="utf-8", mode="w")
handler.setFormatter(logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)

# Make the class inherit from commands.Cog
class TreacheryPokemon(commands.Cog):
    def __init__(self, bot):
        self.bot, self.current_pokemon, self.current_sprite, self.base_url, self.pokemon_count = bot, None, None, "https://pokeapi.co/api/v2/pokemon/", 1025
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_guild(spawn_channel=None, spawn_rate=0.0)
        self.spawn_message, self.pokemon_id = None, None
        self.conn = sqlite3.connect(cog_data_path(self) / 'pokemon.db')
        self.cur = self.conn.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS pokedex (member_id INTEGER, pokemon_id INTEGER, pokemon_name VARCHAR, poketag VARCHAR (5), experience INTEGER, PRIMARY KEY (member_id, pokemon_id))')
        self.cur.execute('CREATE TABLE IF NOT EXISTS party (member_id INTEGER, position1 TEXT, position2 TEXT, position3 TEXT, position4 TEXT, position5 TEXT)')
        self.conn.commit()

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.command()
    async def setpokemonspawn(self, ctx, channel: commands.TextChannelConverter, spawn_rate: float):
        await self.config.guild(ctx.guild).spawn_channel.set(channel.id)
        await self.config.guild(ctx.guild).spawn_rate.set(spawn_rate / 100)
        await ctx.send(f"Pokémon will now spawn in {channel.mention} with a spawn rate of {spawn_rate}% per message.")

    @commands.command()
    @commands.is_owner()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def spawn(self, ctx):
        spawn_channel = discord.utils.get(ctx.guild.channels, id=await self.config.guild(ctx.guild).spawn_channel())
        if ctx.channel == spawn_channel:
            pokemon_id = random.randint(1, self.pokemon_count)
            pokemon_url = self.base_url + str(pokemon_id)
            response = requests.get(pokemon_url)
            if response.status_code == 200:
                pokemon_data = response.json()
                self.current_pokemon, self.current_sprite = pokemon_data['name'], pokemon_data['sprites']['other']['official-artwork']['front_default']
                image_data = BytesIO (requests.get (self.current_sprite).content)
                image_file = discord.File (image_data, filename="pokemon.png")
                embed_dict = {"title": "A wild Pokemon has appeared!", "image": {"url": "attachment://pokemon.png"}}
                embed = discord.Embed.from_dict(embed_dict)
                message = await ctx.send(file=image_file, embed=embed)
                self.spawn_message = message
                self.pokemon_id = message.embeds[0].description
            else:
                await ctx.send("Failed to spawn a Pokémon. Please try again.")

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
            poketag, experience = secrets.token_hex(3), 0
            self.cur.execute('INSERT INTO pokedex (member_id, pokemon_id, pokemon_name, poketag, experience) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, self.pokemon_id, self.current_pokemon, poketag, experience))
            self.conn.commit()
            if self.spawn_message:
                new_embed = discord.Embed(title="Pokemon Caught", description=f"{self.current_pokemon.capitalize()} was caught by {ctx.author.name}.")
                await self.spawn_message.edit(embed=new_embed)
            self.current_pokemon, self.current_sprite, self.spawn_message = None, None, None
        else:
            await ctx.send("That is not the correct Pokémon name or there is no Pokémon to catch. Use the `spawn` command to spawn one.")

    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        self.cur.execute('SELECT pokemon_id, pokemon_name, poketag, experience FROM pokedex WHERE member_id = ?', (ctx.author.id,))
        pokedex = self.cur.fetchall()
        if pokedex:
            embeds = [self.create_embed(chunk) for chunk in (pokedex[i:i+10] for i in range(0, len(pokedex), 10))]
            view = PokedexView(ctx, embeds, 10, pokedex)
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

    def create_embed(self, chunk):
        embed = discord.Embed(title="Your Pokedex", color=discord.Color.random())
        for pokemon_id, pokemon_name, poketag, experience in chunk:
            if poketag is None:
                poketag = secrets.token_hex(3)
                self.cur.execute('UPDATE pokedex SET poketag = ? WHERE member_id = ? AND pokemon_id = ?', (poketag, ctx.author.id, pokemon_id))
                self.conn.commit()
            embed.add_field(name=f"{pokemon_name.capitalize()}", value=f"Poketag: {poketag.upper()}\nEXP: {experience}", inline=True)
        return embed

class PokedexView(discord.ui.View):
    def __init__(self, ctx, embeds, pokemon_per_page, pokedex):
        super().__init__(timeout=None)
        self.ctx, self.embeds, self.current, self.pokemon_per_page, self.pokedex = ctx, embeds, 0, pokemon_per_page, pokedex
        self.total = (len(self.pokedex) + pokemon_per_page - 1) // pokemon_per_page
        self.update_footer()

    def update_footer(self):
        self.embeds[self.current].set_footer(text=f"Showing Pokémon {self.current * self.pokemon_per_page + 1} - {min((self.current + 1) * self.pokemon_per_page, len(self.pokedex))} of {len(self.pokedex)}")

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction, button):
        if interaction.user == self.ctx.author:
            await interaction.response.defer()
            self.current -= 1
            if self.current < 0:
                self.current = self.total - 1
            self.update_footer()
            try:
                await interaction.message.edit(embed=self.embeds[self.current])
            except Exception as e:
                print(e)
        else:
            try:
                await interaction.response.send_message("Only the author of the command can use this button.", ephemeral=True)
            except Exception as e:
                print(e)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction, button):
        if interaction.user == self.ctx.author:
            await interaction.response.defer()
            self.current += 1
            if self.current >= self.total:
                self.current = 0
            self.update_footer()
            try:
                await interaction.message.edit(embed=self.embeds[self.current])
            except Exception as e:
                print(e)
        else:
            try:
                await interaction.response.send_message("Only the author of the command can use this button.", ephemeral=True)
            except Exception as e:
                print(e)

# Add a setup function to register the cog with the bot
def setup(bot):
    bot.add_cog(TreacheryPokemon(bot))