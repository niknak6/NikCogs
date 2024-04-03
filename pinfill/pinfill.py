@tasks.loop(hours=3)
async def storm_check(self):
    eastern = pytz.timezone('US/Eastern')
    current_time = datetime.now(eastern)
    if current_time.hour in [2, 5, 8, 11] and current_time.minute == 30:
        for guild in self.bot.guilds:
            channel_id = await self.config.guild(guild).channel()
            ping_user_id = await self.config.guild(guild).ping_user()
            if channel_id:
                channel = guild.get_channel(channel_id)
                if channel:
                    url = "https://www.wowhead.com/today-in-wow"
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            if response.status == 200:
                                html = await response.text()
                                start_index = html.find('[{"class":"elemental-storm')
                                end_index = html.find('}]', start_index) + 2
                                if start_index != -1 and end_index != -1:
                                    json_str = html[start_index:end_index]
                                    try:
                                        data = json.loads(json_str)
                                        active_storms = []
                                        for item in data:
                                            if 'class' in item:
                                                if 'tiw-upcoming' not in item['class']:
                                                    zone = item['name']
                                                    timer = item.get('ending', 'N/A')
                                                    element = item['class'].split('-')[-1].capitalize()
                                                    if (zone == "Ohn'ahran Plains" and element == "Fire") or \
                                                       (zone == "Thaldraszus" and element == "Air"):
                                                        active_storms.append(f"{zone} ({element}): {timer}")
                                        if active_storms:
                                            message = "Active Elemental Storms:\n"
                                            message += "\n".join(active_storms)
                                            if ping_user_id:
                                                ping_user = guild.get_member(ping_user_id)
                                                if ping_user:
                                                    message = f"{ping_user.mention}\n{message}"
                                            try:
                                                await channel.send(message)
                                            except discord.HTTPException as e:
                                                # Handle the exception here
                                                print(f"Error sending message: {e}")
                                    except json.JSONDecodeError:
                                        # Handle the JSON decoding error here
                                        print("Error decoding JSON data from WoWhead")