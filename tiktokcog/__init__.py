from .tiktokcog import TikTokCog


async def setup(bot):
    await bot.add_cog(TikTokCog(bot))
