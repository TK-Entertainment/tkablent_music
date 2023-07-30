import discord

class EmojiClass():
    @property
    def FirstPage(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('⏪')
    
    @property
    def PrevPage(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('⬅️')
    
    @property
    def NextPage(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('➡️')
    
    @property
    def Skip(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('⏩')

    @property
    def LastPage(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('⏩')
    
    @property
    def Pause(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('⏸️')
    
    @property
    def Play(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('▶️')
    
    @property
    def Stop(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('⏹️')
    
    @property
    def Repeat(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('🔁')
    
    @property
    def SingleRepeat(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('🔂')
    
    @property
    def Shuffle(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('🔀')
    
    @property
    def Bulb(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('💡')
    
    @property
    def Queue(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('🗒️')
    
    @property
    def Leave(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str("📤")
    
    @property
    def Search(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str("🔎")
    
    @property
    def End(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('❎')
    
    @property
    def Done(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('✅')
    
    @property
    def Loading(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('<a:loading:696701361504387212>')
    
    @property
    def Caution(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('⚠️')
    
    @property
    def YouTube(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('<:youtube:1010812724009242745>')
    
    @property
    def SoundCloud(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('<:soundcloud:1010812662155837511>')
    
    @property
    def Spotify(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('<:spotify:1010844746647883828>')
    
    @property
    def Rescue(self) -> discord.PartialEmoji:
        return discord.PartialEmoji.from_str('🛟')

Emoji = EmojiClass()