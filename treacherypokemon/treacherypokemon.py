from redbot.core import commands, Config
from redbot.core.data_manager import cog_data_path
import sqlite3
from typing import Dict, List, Any
import random, requests, secrets, discord
from discord.utils import get
from redbot.core.commands.converter import Optional
from discord import Embed, Reaction
import datetime
import asyncio
import aiohttp
import traceback
from PIL import Image, ImageFilter, ImageEnhance, ImageSequence
from io import BytesIO

class TreacheryPokemon(commands.Cog):
    """Interacts with a database for querying, updating, and managing Pokemon-related functionalities."""
    
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect(cog_data_path(self) / 'pokemon.db')
        self.current_pokemon, self.current_sprite = None, None
        self.base_url = "https://pokeapi.co/api/v2/pokemon/"
        self.type_url = "https://pokeapi.co/api/v2/type/"
        self.pokemon_count = 1025
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)
        self.config.register_guild(spawn_channel=None, spawn_rate=0.0, spawn_cooldown=15.0)
        self.spawn_message, self.pokemon_id = None, None
        self.last_spawn = None
        self.trades = {}
        self.battles = {}
        self.rate_limit_lock = asyncio.Lock()
        
        # Database setup
        self.cur = self.conn.cursor()
        self.cur.execute('CREATE TABLE IF NOT EXISTS pokedex (member_id INTEGER, pokemon_id INTEGER, pokemon_name VARCHAR, level INTEGER, poketag VARCHAR (5), experience INTEGER, PRIMARY KEY (member_id, pokemon_id))')
        self.cur.execute('CREATE TABLE IF NOT EXISTS party (member_id INTEGER, position1 TEXT, position2 TEXT, position3 TEXT, position4 TEXT, position5 TEXT, position6 TEXT, PRIMARY KEY (member_id))')
        self.conn.commit()

    def cog_unload(self):
        self.conn.close()

    async def execute_query(self, query: str, values: tuple = ()) -> List[Dict[str, Any]]:
        """Executes a query and returns the results as a list of dictionaries."""
        try:
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(query, values)
                return [dict(zip((col[0] for col in cursor.description), row)) 
                        for row in cursor.fetchall()] if query.lower().startswith("select") else []
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
        return []

    @commands.command(name="querydb")
    async def query_db(self, ctx, table: str, columns: str, *, filters: str = ""):
        """Queries the database based on provided table, columns, and filters, supporting case-insensitive searches and comparison operators."""
        columns_query_part = ", ".join(column.strip() for column in columns.split(','))
        query = f"SELECT {columns_query_part} FROM {table}"
        filter_conditions = []
        filter_values = []

        for filter_item in filters.split(" AND "):
            for operator in [">=", "<=", ">", "<", "=", "!="]:
                if operator in filter_item:
                    column, value = map(str.strip, filter_item.split(operator))
                    value = value.lower().replace("*", "%")
                    filter_conditions.append(f"LOWER({column}) {'LIKE' if '%' in value else operator} ?")
                    filter_values.append(value)
                    break

        if filter_conditions:
            query += f" WHERE {' AND '.join(filter_conditions)}"

        result = await self.execute_query(query, tuple(filter_values))
        if not result:
            await ctx.send("No results found.")
            return

        result_str = str(result)
        char_limit = 2000
        for chunk in [result_str[i:i+char_limit] for i in range(0, len(result_str), char_limit)]:
            await ctx.send(chunk)

    @commands.command(name="updatedb")
    @commands.is_owner()
    async def update_db(self, ctx, table: str, field: str, value: str, **filters: str):
        """Updates a field in the database based on provided table, field, value, and filters."""
        # Ensure the command is only usable by the bot owner
        query = f"UPDATE {table} SET {field} = ? WHERE {' AND '.join(f'{k} = ?' for k in filters) or '1=1'}"
        await self.execute_query(query, (*filters.values(), value))
        await ctx.send("Update successful.")

    def get_random_move(self, ctx, pokemon_name):
        member_id = ctx.author.id
        self.cur.execute('SELECT level FROM pokedex WHERE member_id = ? AND pokemon_name = ?', (member_id, pokemon_name))
        result = self.cur.fetchone()
        pokemon_level = result[0] if result else 1

        pokemon_url = f"{self.base_url}{pokemon_name.lower().replace(' ', '-').replace('.', '')}"
        try:
            pokemon_data = requests.get(pokemon_url).json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching Pokémon data: {e}")
            return "NULL", "NULL", 0

        blacklisted_moves = {
            'after-you', 'quash', 'helping-hand', 'ally-switch', 
            'follow-me', 'rage-powder', 'aromatic-mist', 
            'hold-hands', 'spotlight'
        }

        valid_moves = [
            move for move in pokemon_data['moves']
            if move['move']['name'] not in blacklisted_moves and
            any(
                vg['level_learned_at'] <= pokemon_level and
                vg['move_learn_method']['name'] == 'level-up'
                for vg in move['version_group_details']
            )
        ]

        moves_with_power = []
        for move in valid_moves:
            try:
                move_data = requests.get(move['move']['url']).json()
                if move_data.get('power'):
                    moves_with_power.append(move)
            except requests.exceptions.RequestException as e:
                print(f"Error fetching move data: {e}")

        if not moves_with_power:
            return "NULL", "NULL", 0

        selected_move = random.choice(moves_with_power)
        try:
            move_data = requests.get(selected_move['move']['url']).json()
            move_power = move_data.get('power', 0)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching selected move data: {e}")
            return "NULL", "NULL", 0

        return selected_move['move']['name'], move_data['type']['name'], move_power

    def get_pokemon_health(self, member_id, pokemon_name):
        self.cur.execute('SELECT poketag, level FROM pokedex WHERE member_id = ? AND pokemon_name = ?', (member_id, pokemon_name))
        result = self.cur.fetchone()
        pokemon_level = result[1] if result else 1

        pokemon_url = f"{self.base_url}{pokemon_name.lower().replace(' ', '-').replace('.', '')}"
        try:
            response = requests.get(pokemon_url)
            response.raise_for_status()
            base_hp = response.json()['stats'][0]['base_stat']
        except (requests.exceptions.HTTPError, requests.exceptions.JSONDecodeError, Exception) as e:
            print(f"Error occurred: {e}")
            base_hp = 10

        hp = round(((base_hp * 2) * pokemon_level / 100) + pokemon_level + 10)
        return hp

    async def on_command_error(self, ctx: commands.Context, error):
        # Handle your errors here
        if isinstance(error, commands.MemberNotFound):
            await ctx.send(f"I could not find member '{error.argument}'. Please try again")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"'{error.param.name}' is a required argument.")
        elif isinstance(error, commands.CommandError):
            await ctx.send(error) # Send the error message to the context channel
        else:
            # All unhandled errors will print their original traceback
            print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.command()
    async def setpokemonspawn(self, ctx, channel: commands.TextChannelConverter, spawn_rate: float, cooldown: Optional[float] = 15.0): # added cooldown argument
        await self.config.guild(ctx.guild).spawn_channel.set(channel.id)
        await self.config.guild(ctx.guild).spawn_rate.set(spawn_rate / 100)
        await self.config.guild(ctx.guild).spawn_cooldown.set(cooldown)
        await ctx.send(f"Pokémon will now spawn in {channel.mention} with a spawn rate of {spawn_rate}% per message and a cooldown of {cooldown} minutes.") # updated confirmation message

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.channel)
    async def spawn(self, ctx):
        if ctx.invoked_with == "spawn" and not await self.bot.is_owner(ctx.author):
            await ctx.send("Only the owner of the bot can manually spawn a Pokémon.")
            return
        spawn_channel = discord.utils.get(ctx.guild.channels, id=await self.config.guild(ctx.guild).spawn_channel())
        spawn_cooldown = await self.config.guild(ctx.guild).spawn_cooldown()
        if ctx.channel == spawn_channel:
            now = datetime.datetime.now()
            if self.last_spawn is None or (now - self.last_spawn).total_seconds() >= spawn_cooldown * 60 or await self.bot.is_owner(ctx.author):
                pokemon_id = random.randint(1, self.pokemon_count)
                pokemon_url = self.base_url + str(pokemon_id)
                response = requests.get(pokemon_url)
                if response.status_code == 200:
                    pokemon_data = response.json()
                    self.current_pokemon, self.current_sprite = pokemon_data['name'], pokemon_data['sprites']['other']['official-artwork']['front_default']
                    self.pokemon_id = pokemon_data['id']
                    image_data = BytesIO(requests.get(self.current_sprite).content)
                    image_file = discord.File(image_data, filename="pokemon.png")
                    embed_dict = {"title": "A wild Pokémon has appeared!", "image": {"url": "attachment://pokemon.png"}}
                    embed = discord.Embed.from_dict(embed_dict)
                    message = await ctx.send(file=image_file, embed=embed)
                    self.spawn_message = message
                    self.last_spawn = now
                else:
                    await ctx.send("Failed to spawn a Pokémon. Please try again.")
        else:
            raise commands.CheckFailure("You are not the owner of this bot.")

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        if message.author.bot or not message.guild:
            return
        spawn_channel = discord.utils.get(message.guild.channels, id=await self.config.guild(message.guild).spawn_channel())
        spawn_rate = await self.config.guild(message.guild).spawn_rate()
        spawn_cooldown = await self.config.guild(message.guild).spawn_cooldown()
        now = datetime.datetime.now()
        if message.channel == spawn_channel:
            if random.random() < spawn_rate and (self.last_spawn is None or (now - self.last_spawn).total_seconds() >= spawn_cooldown * 60):
                ctx = await self.bot.get_context(message)
                ctx.message.content = (ctx.prefix or "!") + "spawn"
                await self.bot.get_command("spawn").invoke(ctx)
            else:
                await self.update_experience_and_level(message)

    async def update_experience_and_level(self, message):
        self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (message.author.id,))
        user_party = self.cur.fetchone()
        leveled_up = []
        if user_party:
            for position in user_party:
                if position != '-':
                    poketag = position.lower()
                    self.cur.execute('SELECT level, experience FROM pokedex WHERE member_id = ? AND poketag = ?', (message.author.id, poketag))
                    level, experience = self.cur.fetchone()
                    messages_required = round(0.02 * level ** 2 + 0.2 * level + 1)
                    if experience >= messages_required:
                        level += 1
                        experience = 0
                        self.cur.execute('UPDATE pokedex SET level = ?, experience = ? WHERE member_id = ? AND poketag = ?', (level, experience, message.author.id, poketag))
                        self.conn.commit()
                        pokemon_name = self.get_pokemon_name(message.author.id, poketag)
                        if level in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
                            leveled_up.append((pokemon_name, level))
                    else:
                        experience += 1
                        self.cur.execute('UPDATE pokedex SET experience = ? WHERE member_id = ? AND poketag = ?', (experience, message.author.id, poketag))
                        self.conn.commit()
            if leveled_up:
                output = "\n".join([f"{pokemon_name.capitalize()} has leveled up to level {level}!" for pokemon_name, level in leveled_up])
                await message.channel.send(f"{message.author.mention}, your Pokémon have leveled up!\n\n{output}")

    def get_pokemon_name(self, member_id, poketag):
        self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (member_id, poketag))
        return self.cur.fetchone()[0]

    @commands.guild_only()
    @commands.command(name="catch")
    async def pokecatch(self, ctx, *, pokemon: str):
        pokemon = pokemon.replace(" ", "-").lower()
        if self.current_pokemon:
            api_pokemon_name = self.current_pokemon.lower().replace(" ", "-").replace(".", "")
            if pokemon in api_pokemon_name or api_pokemon_name in pokemon:
                await ctx.send(f"Congratulations! You caught a {self.current_pokemon.capitalize()}!")
                level, experience = 1, 0
                poketag = secrets.token_hex(3)
                pokemon_name = self.current_pokemon.title()
                self.cur.execute('INSERT INTO pokedex (member_id, pokemon_id, pokemon_name, level, poketag, experience) VALUES (?, ?, ?, ?, ?, ?)', (ctx.author.id, self.pokemon_id, pokemon_name, level, poketag, experience))
                self.conn.commit()
                if self.spawn_message:
                    new_embed = discord.Embed(title="Pokemon Caught", description=f"{pokemon_name} was caught by {ctx.author.name}.")
                    await self.spawn_message.edit(embed=new_embed)
                self.current_pokemon, self.current_sprite, self.spawn_message = None, None, None
            else:
                await ctx.send("That is not the correct Pokémon name or there is no Pokémon to catch.")

    @commands.guild_only()
    @commands.command()
    async def freepokemon(self, ctx, poketag: str):
        """Free a Pokémon from your Pokédex by its Poketag."""
        self.cur.execute('SELECT pokemon_id, pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower()))
        pokemon_data = self.cur.fetchone()
        if pokemon_data is None:
            await ctx.send("You do not have that Pokémon in your Pokédex.")
            return
        pokemon_id, pokemon_name = pokemon_data
        self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (ctx.author.id,))
        user_party = self.cur.fetchone()
        if user_party is not None and poketag.lower() in user_party:
            await ctx.send("You cannot free a Pokémon that is in your party.")
            return
        self.cur.execute('DELETE FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower()))
        self.conn.commit()
        await ctx.send(f"You have freed your {pokemon_name.capitalize()} from your Pokédex.")

    @commands.guild_only()
    @commands.command()
    async def pokedex(self, ctx):
        self.cur.execute('SELECT pokemon_id, pokemon_name, poketag, level, experience FROM pokedex WHERE member_id = ? ORDER BY pokemon_id', (ctx.author.id,))
        pokedex = self.cur.fetchall()
        if pokedex:
            embeds = [self.create_embed(ctx, chunk) for chunk in (pokedex[i:i+15] for i in range(0, len(pokedex), 15))]
            view = PokedexView(ctx, embeds, pokedex)
            view.timeout = 300
            await ctx.send(embed=embeds[0], view=view)
        else:
            await ctx.send("You have not caught any Pokémon yet.")

    def create_embed(self, ctx, chunk):
        embed = discord.Embed(title=f"{ctx.author.name}'s Pokédex", color=discord.Color.random())
        for pokemon_id, pokemon_name, poketag, level, experience in chunk:
            if poketag is None:
                poketag = secrets.token_hex(3)
                self.cur.execute('UPDATE pokedex SET poketag = ? WHERE member_id = ? AND pokemon_id = ?', (poketag, ctx.author.id, pokemon_id))
                self.conn.commit()
            pokemon_name_formatted = "{} (#{})".format(pokemon_name.capitalize(), pokemon_id)
            messages_required = round(0.02 * level ** 2 + 0.2 * level + 1)
            experience_fraction = f"{experience}/{messages_required}"
            
            # Add the Pokémon's details to the embed field without HP
            embed.add_field(name=pokemon_name_formatted, value=f"Poketag: {poketag.upper()}\nLevel: {level}\nEXP: {experience_fraction}", inline=True)
        return embed

    @commands.guild_only()
    @commands.command()
    async def party(self, ctx, *poketags: str):
        if len(poketags) == 0:
            self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (ctx.author.id,))
            current_party = self.cur.fetchone()
            if current_party is not None:
                pokemon_data = [self.cur.execute('SELECT pokemon_name, level, experience FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower())).fetchone() for poketag in current_party if poketag != '-']
                experience = [exp for _, _, exp in pokemon_data]
                messages_required = [round(0.02 * level ** 2 + 0.2 * level + 1) for _, level, _ in pokemon_data]
                experience_left = [required - exp for required, exp in zip(messages_required, experience)]
                experience_fraction = [f"{exp}/{required}" for exp, required in zip(experience, messages_required)]
                output = [f"{poketag.upper()} - {pokemon_name.capitalize()} (Level {level}, EXP {exp_frac})" for poketag, (pokemon_name, level, _), exp_frac in zip(current_party, pokemon_data, experience_fraction)]
                output = "\n".join(output)
                embed = discord.Embed(title=f"{ctx.author.name}'s Party", description=output, color=discord.Color.random())
                await ctx.send(embed=embed)
            else:
                await ctx.send("You don't have a party yet.")
        elif len(poketags) != 6:
            await ctx.send("You must provide exactly 6 Pokétags.")
        else:
            self.cur.execute('SELECT poketag FROM pokedex WHERE member_id = ?', (ctx.author.id,))
            user_poketags = [row[0] for row in self.cur.fetchall()]
            if all(poketag.lower() in user_poketags or poketag == '-' for poketag in poketags):
                self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (ctx.author.id,))
                current_party = self.cur.fetchone()

                if current_party is not None:
                    positions = dict(zip(['position1', 'position2', 'position3', 'position4', 'position5', 'position6'], poketags))

                    columns = []
                    values = []
                    for column, value in positions.items():
                        if value != '-':
                            columns.append(f"{column} = ?")
                            values.append(value)
                    columns = ", ".join(columns)
                    values.append(ctx.author.id)
                    self.cur.execute(f'UPDATE party SET {columns} WHERE member_id = ?', values)
                    self.conn.commit()
                    await ctx.send("Your party has been updated.")
                else:
                    self.cur.execute('INSERT INTO party (member_id, position1, position2, position3, position4, position5, position6) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                                    (ctx.author.id, *poketags))
                    self.conn.commit()
                    await ctx.send("Your party has been created.")
            else:
                await ctx.send("You do not have all of these Pokétags in your Pokédex.")

    @commands.guild_only()
    @commands.command()
    async def trade(self, ctx, user: commands.MemberConverter, poketag: str):
        """Initiate and complete a trade with another user."""
        # Initiate the trade
        self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (ctx.author.id, poketag.lower()))
        pokemon_name = self.cur.fetchone()
        if pokemon_name is None:
            await ctx.send("You do not have that Pokémon in your Pokédex.")
            return
        if user == ctx.author:
            await ctx.send("You cannot trade with yourself.")
            return
        trade_message = await ctx.send(f"{user.mention}, {ctx.author.name} wants to trade their {pokemon_name[0].capitalize()} to you. Please reply with the Poketag of the Pokémon you are offering.")
        if not hasattr(self, "trades"):
            self.trades = {}
        self.trades[trade_message.id] = {"sender": ctx.author, "receiver": user, "sender_poketag": poketag.lower(), "receiver_poketag": None}

        # Wait for the receiver's response
        def check(m):
            return m.author == user and m.reference and m.reference.message_id == trade_message.id

        try:
            response = await self.bot.wait_for('message', check=check, timeout=300)  # Wait for 5 minutes
        except asyncio.TimeoutError:
            await ctx.send("Trade request timed out.")
            del self.trades[trade_message.id]
            return

        # Complete the trade
        poketag = response.content.lower()
        self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (user.id, poketag))
        pokemon_name = self.cur.fetchone()
        if pokemon_name is None:
            await ctx.send("You do not have that Pokémon in your Pokédex.")
            return
        self.trades[trade_message.id]["receiver_poketag"] = poketag
        trade = self.trades[trade_message.id]
        self.cur.execute('UPDATE pokedex SET member_id = ? WHERE member_id = ? AND poketag = ?', (trade["receiver"].id, trade["sender"].id, trade["sender_poketag"]))
        self.cur.execute('UPDATE pokedex SET member_id = ? WHERE member_id = ? AND poketag = ?', (trade["sender"].id, trade["receiver"].id, trade["receiver_poketag"]))
        self.conn.commit()
        await ctx.send(f"The trade between {trade['sender'].name} and {trade['receiver'].name} was completed successfully.")
        del self.trades[trade_message.id]
    
    # Define the on_command_error event handler
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        # Handle your errors here
        if isinstance(error, commands.CommandError):
            await ctx.send(error) # Send the error message to the context channel
        else:
            # All unhandled errors will print their original traceback
            print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        
    async def combatsprite(self, ctx, player1_pokemon_name, player2_pokemon_name):
        # Helper function to fetch and process sprites
        async def fetch_sprite(pokemon_name, sprite_type):
            sprite_url = f"{self.base_url}{pokemon_name.lower().replace(' ', '-').replace('.', '')}"
            async with aiohttp.ClientSession() as session:
                async with session.get(sprite_url) as response:
                    if response.status != 200:
                        raise ValueError(f"Failed to fetch sprite URL: {sprite_url}")
                    data = await response.json()
                    
                    # Try to get the sprite from 'showdown' first
                    sprite = data['sprites']['other']['showdown'].get(sprite_type)
                    
                    # Fallback to 'sprites' if 'showdown' sprite is not available
                    if not sprite:
                        sprite = data['sprites'].get(sprite_type)
                    
                    # Fallback to 'official-artwork' if neither 'showdown' nor 'sprites' are available
                    if not sprite:
                        sprite = data['sprites']['other']['official-artwork'].get('front_default')
                    
                    if not sprite:
                        raise ValueError(f"Sprite type '{sprite_type}' not found for {pokemon_name}")
                    
                    async with session.get(sprite) as sprite_response:
                        if sprite_response.status != 200:
                            raise ValueError(f"Failed to fetch sprite image: {sprite}")
                        return Image.open(BytesIO(await sprite_response.read()))

        # Fetch and process sprites
        player1_sprite_image = await fetch_sprite(player1_pokemon_name, 'back_default')
        player2_sprite_image = await fetch_sprite(player2_pokemon_name, 'front_default')

        # Create a list to hold all frames of the combined GIF
        combined_frames = []

        # Extract frames from both GIFs
        player1_frames = [frame.copy() for frame in ImageSequence.Iterator(player1_sprite_image)]
        player2_frames = [frame.copy() for frame in ImageSequence.Iterator(player2_sprite_image)]

        # Ensure both GIFs have the same number of frames by repeating frames
        num_frames = max(len(player1_frames), len(player2_frames))
        player1_frames = (player1_frames * (num_frames // len(player1_frames) + 1))[:num_frames]
        player2_frames = (player2_frames * (num_frames // len(player2_frames) + 1))[:num_frames]

        # Resize individual frames before combining
        player1_frames = [frame.resize((int(frame.width * 0.75), int(frame.height * 0.75)), Image.Resampling.LANCZOS) for frame in player1_frames]
        player2_frames = [frame.resize((int(frame.width * 0.75), int(frame.height * 0.75)), Image.Resampling.LANCZOS) for frame in player2_frames]

        for player1_frame, player2_frame in zip(player1_frames, player2_frames):
            # Create a new image with a width and height that accommodates both sprites
            total_width = max(player1_frame.width, player2_frame.width) * 2
            total_height = max(player1_frame.height, player2_frame.height) * 2
            combined_frame = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))  # Ensure transparency

            # Paste player1's sprite in the bottom left quadrant
            combined_frame.paste(player1_frame.convert('RGBA'), (0, total_height // 2), player1_frame.convert('RGBA'))

            # Paste player2's sprite in the top right quadrant
            combined_frame.paste(player2_frame.convert('RGBA'), (total_width // 2, 0), player2_frame.convert('RGBA'))

            # Enhance colors
            enhancer = ImageEnhance.Color(combined_frame)
            combined_frame = enhancer.enhance(1.2)  # Increase color saturation by 20%

            # Append the combined frame to the list
            combined_frames.append(combined_frame)

        # Save the combined frames as a GIF to a BytesIO object
        combined_image_io = BytesIO()
        combined_frames[0].save(
            combined_image_io, 
            format='GIF', 
            save_all=True, 
            append_images=combined_frames[1:], 
            loop=0, 
            duration=player1_sprite_image.info.get('duration', 100),
            disposal=2  # Ensure that the previous frame is cleared before drawing the next frame
        )
        combined_image_io.seek(0)
        combined_image_file = discord.File(combined_image_io, filename='combined_sprite.gif')

        # Send the combined GIF file
        await ctx.send(file=combined_image_file)
    
    @commands.command()
    async def battle(self, ctx, opponent: discord.Member):
        if opponent.bot or ctx.author.id in self.battles or opponent.id in self.battles:
            return await ctx.send("Cannot start battle due to one of the conditions not being met.")

        def fetch_party(member_id):
            return [self.cur.execute('SELECT pokemon_name FROM pokedex WHERE member_id = ? AND poketag = ?', (member_id, tag.lower())).fetchone()[0]
                    for tag in self.cur.execute('SELECT position1, position2, position3, position4, position5, position6 FROM party WHERE member_id = ?', (member_id,)).fetchone()
                    if tag != '-']

        player1_party, player2_party = fetch_party(ctx.author.id), fetch_party(opponent.id)
        if not all([player1_party, player2_party]):
            raise commands.CommandError("Both players must have a party.")

        player1_hp = {pokemon: self.get_pokemon_health(ctx.author.id, pokemon) for pokemon in player1_party}
        player2_hp = {pokemon: self.get_pokemon_health(opponent.id, pokemon) for pokemon in player2_party}

        player1_pokemon_name, player2_pokemon_name = player1_party[0], player2_party[0]
        combined_image_file = await self.combatsprite(ctx, player1_pokemon_name, player2_pokemon_name)  # Await the coroutine here

        # Check if combined image file is ready
        if not combined_image_file:
            return await ctx.send("Failed to generate battle image. Please try again later.")

        turn_number = 1
        battle_embed = discord.Embed(title=f"Battle: {ctx.author.display_name} VS {opponent.display_name}")
        battle_embed.add_field(name="Turn", value=turn_number, inline=False)
        battle_embed.add_field(name=f"{player1_pokemon_name} HP", value="Loading...", inline=True)
        battle_embed.add_field(name=f"{player2_pokemon_name} HP", value="Loading...", inline=True)
        battle_embed.add_field(name="Defeated Pokémon", value="None", inline=False)
        battle_embed.add_field(name="Moves", value="Waiting...", inline=False)

        # Set the image URL in the embed
        battle_embed.set_image(url=f"attachment://{combined_image_file.filename}")

        # Send the initial message with the embed and the image file
        battle_message = await ctx.send(embed=battle_embed, file=combined_image_file)

        await battle_message.add_reaction("⚔️")
        self.battles[ctx.author.id], self.battles[opponent.id] = opponent.id, ctx.author.id

        async def fetch_pokemon_type(pokemon_name):
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}{pokemon_name.lower().replace(' ', '-').replace('.', '')}") as resp:
                    return [t['type']['name'] for t in (await resp.json())['types']]

        multipliers = {'double_damage_to': 2.0, 'half_damage_to': 0.5, 'no_damage_to': 0.0}

        defeated_pokemon = []

        while player1_party and player2_party:
            moves_display = ""

            for player_party, player_hp, player_display, opponent_party, opponent_hp, opponent_display in [
                (player1_party, player1_hp, ctx.author.display_name, player2_party, player2_hp, opponent.display_name),
                (player2_party, player2_hp, opponent.display_name, player1_party, player1_hp, ctx.author.display_name)
            ]:
                if not player_party:
                    continue

                pokemon, move, type_, move_power = player_party[0], *self.get_random_move(ctx, player_party[0])
                move_power = move_power or 0

                async with aiohttp.ClientSession() as session:
                    response = await session.get(f"{self.type_url}{type_}")
                    damage_relations = (await response.json()).get('damage_relations', {}) if response.status == 200 else {}

                opposing_pokemon_name = opponent_party[0]
                opposing_types = await fetch_pokemon_type(opposing_pokemon_name)

                multiplier = max((multipliers.get(key, 1.0) for key in multipliers if any(opposing_type in [relation['name'] for relation in damage_relations.get(key, [])] for opposing_type in opposing_types)), default=1.0)
                damage = 10 if move_power == 0 else move_power * multiplier

                opponent_hp[opponent_party[0]] = max(opponent_hp[opponent_party[0]] - damage, 0)

                hp_field_index = 1 if player_display == ctx.author.display_name else 2
                battle_embed.set_field_at(hp_field_index, name=f"{pokemon} HP", value=f"{round(player_hp[pokemon])}", inline=True)
                formatted_move_name = "No move available" if move == "NULL" else ' '.join(word.capitalize() for word in move.replace('-', ' ').split())
                moves_display += f"{player_display}'s {pokemon}: {formatted_move_name} - Damage: {damage} ({multiplier}x)\n"

                battle_embed.set_field_at(4, name="Moves", value=moves_display, inline=False)

                # Update the battle embed after each move
                await battle_message.edit(embed=battle_embed)

                if opponent_hp[opponent_party[0]] <= 0:
                    defeated_pokemon.append(f"{opponent_party[0]} ({opponent_display})")
                    opponent_party.pop(0)
                    moves_display += f"{opponent_display}'s {opposing_pokemon_name} has been defeated!\n"
                    battle_embed.set_field_at(4, name="Moves", value=moves_display, inline=False)
                    battle_embed.set_field_at(3, name="Defeated Pokémon", value='\n'.join(defeated_pokemon), inline=False)
                    if opponent_party:
                        new_pokemon = opponent_party[0]
                        player1_pokemon_name, player2_pokemon_name = (new_pokemon, player2_pokemon_name) if opponent_display == ctx.author.display_name else (player1_pokemon_name, new_pokemon)
                        combined_image_file = await self.combatsprite(ctx, player1_pokemon_name, player2_pokemon_name)  # Await the coroutine here

                        # Check if combined image file is ready
                        if not combined_image_file:
                            return await ctx.send("Failed to generate battle image for new Pokémon. Please try again later.")

                        battle_embed.set_field_at(hp_field_index, name=f"{new_pokemon} HP", value=f"{round(opponent_hp[new_pokemon])}", inline=True)
                        battle_embed.set_image(url=f"attachment://{combined_image_file.filename}")
                        await battle_message.edit(embed=battle_embed, attachments=[combined_image_file])
                    else:
                        break

            async with self.rate_limit_lock:
                turn_number += 1
                battle_embed.set_field_at(0, name="Turn", value=turn_number, inline=False)
                await battle_message.edit(embed=battle_embed)
                await asyncio.sleep(1.5)  # Ensure there's a delay between turns to respect rate limits

        # Determine the winner based on the state of both parties
        if not player1_party and not player2_party:
            winner = "It's a tie!"
        elif not player2_party:
            winner = ctx.author.display_name
        else:
            winner = opponent.display_name

        battle_embed.clear_fields()
        battle_embed.description = f"**{winner} wins the battle!**" if winner != "It's a tie!" else "**It's a tie!**"
        battle_embed.add_field(name="Defeated Pokémon", value='\n'.join(defeated_pokemon) or "None", inline=False)
        battle_embed.set_image(url=None)
        await battle_message.edit(embed=battle_embed)

        # Remove player IDs from self.battles after the battle concludes
        del self.battles[ctx.author.id]
        del self.battles[opponent.id]

class PokedexView(discord.ui.View):
    def __init__(self, ctx, embeds, pokedex):
        super().__init__(timeout=None)
        self.ctx, self.embeds, self.current, self.pokedex, self.total = ctx, embeds, 0, pokedex, len(embeds)

    def update_footer(self):
        start, end = self.current * 10 + 1, min((self.current + 1) * 10, len(self.pokedex))
        self.embeds[self.current].set_footer(text=f"Showing Pokémon {start} - {end} of {len(self.pokedex)}")

    async def handle_button(self, interaction, direction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Only the author of the command can use this button.", ephemeral=True)
        
        await interaction.response.defer()
        self.current = (self.current + direction) % self.total
        self.update_footer()
        await interaction.message.edit(embed=self.embeds[self.current])

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction, button):
        await self.handle_button(interaction, -1)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.blurple)
    async def next(self, interaction, button):
        await self.handle_button(interaction, 1)