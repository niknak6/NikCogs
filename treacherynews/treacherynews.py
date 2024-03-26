from redbot.core import commands, Config
import tiktokpy
from tiktokpy.utils.client import Client

class TreacheryNews(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=1234567890, force_registration=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message contains a TikTok URL
        if "tiktok.com" in message.content:
            await self.download_and_post_video(message)

    async def download_and_post_video(self, message):
        # Initialize TikTokPy client
        async with tiktokpy.TikTokPy() as bot:
            video = await bot.video(id=message.content.split('/')[-1])
            file_path = await video.download()
            
            # Post the video file to the channel where the URL was posted
            with open(file_path, 'rb') as video_file:
                await message.channel.send(file=discord.File(video_file, 'tiktok_video.mp4'))

def setup(bot):
    bot.add_cog(TikTokDownloader(bot))