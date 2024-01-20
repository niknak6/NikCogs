import random
import requests
from redbot.core import commands, Config
import discord
from io import BytesIO # Import BytesIO to convert image data to bytes

class TreacheryPokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.current_pokemon = None
        self.current_sprite = None
        self.base_url = "https://pokeapi.co/api/v2/pokemon/" # Change the base url to the pokemon endpoint
        self.pokemon_count = 1025 # Add an attribute to store the total number of pokemon
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
        self.spawn_message = None # Add an attribute to store the spawn message object

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
            # Generate a random id between 1 and 1025
            pokemon_id = random.randint(1, self.pokemon_count)
            # Use the base url and the id to get the pokemon url
            pokemon_url = self.base_url + str(pokemon_id)
            response = requests.get(pokemon_url)
            if response.status_code == 200:
                pokemon_data = response.json()
                # Get the pokemon name and sprite from the json data
                self.current_pokemon = pokemon_data['name']
                self.current_sprite = pokemon_data['sprites']['other']['official-artwork']['front_default']
                # Use BytesIO to convert the image data to bytes
                image_data = BytesIO (requests.get (self.current_sprite).content)
                # Use discord.File to create a file object from the image data
                image_file = discord.File (image_data, filename="pokemon.png")
                # Change the embed title to "A wild Pokemon has appeared!"
                embed_dict = {
                    "title": "A wild Pokemon has appeared!",
                    # Use the file object as the image url
                    "image": {"url": "attachment://pokemon.png"}
                }
                embed = discord.Embed.from_dict(embed_dict)
                # Send the embed and the file object together
                self.spawn_message = await ctx.send(file=image_file, embed=embed) # Assign the message object to the spawn_message attribute
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
        # Replace the space with a hyphen
        pokemon = pokemon.replace(" ", "-") # This is the change I suggested to fix the issue with spaces in the pokemon name
        if self.current_pokemon and self.current_pokemon == pokemon.lower():
            await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
            pokedex = await self.config.member(ctx.author).pokedex()
            pokedex[self.current_pokemon] = pokedex.get(self.current_pokemon, 0) + 1
            await self.config.member(ctx.author).pokedex.set(pokedex)
            # Edit the spawn embed to remove the image and change the title and description
            if self.spawn_message: # Check if the spawn_message attribute is not None
                new_embed = discord.Embed(title="Pokemon Caught", description=f"{self.current_pokemon.capitalize()} was caught by {ctx.author.name}.") # Create a new embed object with the updated information
                await self.spawn_message.edit(embed=new_embed) # Edit the spawn message with the new embed object
            self.current_pokemon = None
            self.current_sprite = None
            self.spawn_message = None # Reset the spawn_message attribute to None
        else:
            await ctx.send("That is not the correct Pokémon name or there is no Pokémon to catch. Use the `spawn` command to spawn one.")

    class PokedexButton(discord.ui.Button):
        def __init__(self, pokemon_name, pokemon_count):
            super().__init__(style=discord.ButtonStyle.secondary, label=pokemon_name.capitalize(), emoji="🐾")
            self.pokemon_name = pokemon_name
            self.pokemon_count = pokemon_count

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message(f"You have {self.pokemon_count} {self.pokemon_name.capitalize()} in your pokedex.")

    class PokedexView(discord.ui.View):
        def __init__(self, pokedex, timeout=60):
            super().__init__(timeout=timeout)
            self.pokedex = pokedex
            self.buttons = [TreacheryPokemon.PokedexButton(pokemon_name, pokemon_count) for pokemon_name, pokemon_count in pokedex.items()]
            self.current_page = 0
            self.add_buttons(0)

        def add_buttons(self, page):
            self.clear_items()
            start = page * 10
            end = min((page + 1) * 10, len(self.buttons))
            for i in range(start, end):
                self.add_item(self.buttons[i])
            self.add_item(discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, row=4, disabled=page == 0, custom_id="previous"))
            self.add_item(discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, row=4, disabled=page == len(self.buttons) // 10, custom_id="next"))

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, row=4, custom_id="previous")
        async def previous_page(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.current_page -= 1
            self.add_buttons(self.current_page)
            await interaction.message.edit(view=self)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.primary, row=4, custom_id="next")
        async def next_page(self, button: discord.ui.Button, interaction: discord.Interaction):
            self.current_page += 1
            self.add_buttons(self.current_page)
            await interaction.message.edit(view=self)

    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        pokedex = await self.config.member(ctx.author).pokedex()
        if pokedex:
            view = TreacheryPokemon.PokedexView(pokedex)
            await ctx.send(f"{ctx.author.name}'s Pokedex", view=view)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

def setup(bot):
    bot.add_cog(TreacheryPokemon(bot))