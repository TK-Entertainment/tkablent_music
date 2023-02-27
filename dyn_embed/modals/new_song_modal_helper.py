import discord

class NewSongModal(discord.ui.Modal):
    musicbot = self.musicbot

    def __init__(self, requester):
        self.url_or_name = discord.ui.TextInput(
            custom_id="song_url",
            label="歌曲網址或關鍵字 (網址支援 Spotify, SoundCloud)",
            placeholder=f"此歌曲由 {requester} 點播"
        )
        super().__init__(
            title = "🔎 | 搜尋歌曲",
            timeout=120
        )

        self.add_item(self.url_or_name)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await self.musicbot._i_play.callback(self.musicbot, interaction, self.url_or_name.value)