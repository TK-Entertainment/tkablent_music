import sys
sys.path.append("..")
from helpers.playlist_helper import get_current_track, get_playlist
from utils.playlist import LoopState
from dyn_embed.misc import _sec_to_hms
from dyn_embed.icons import caution_emoji
from dyn_embed.data import guild_info, DynEmbedOperation
import discord

def playinfo_generate(guild_id, embed):
    playlist = get_playlist(guild_id)
    queuelist: str = ""
    
    if guild_info(guild_id).operation == DynEmbedOperation.SKIP: # If song is skipped, update songinfo for next song state
        offset = 1
    else:
        offset = 0

    embed.add_field(name="作者", value=f"{playlist.current().author}", inline=True)

    if not playlist.current().is_stream():
        embed.add_field(name="歌曲時長", value=_sec_to_hms(playlist.current().length, "zh"), inline=True)

    if guild_info(guild_id).music_suggestion and len(playlist.order) == 2 and playlist[1].suggested:
        if guild_info(guild_id).operation == DynEmbedOperation.SKIP:
            queuelist += f"**推薦歌曲載入中**"
        else:
            queuelist += f"**【推薦】** {playlist[1].title}"
        embed.add_field(name="{} 即將播放".format(f":hourglass: |" if guild_info(guild_id).operation == DynEmbedOperation.SKIP else ""), value=queuelist, inline=False)
    
    elif len(playlist.order) == 1 and playlist.loop_state == LoopState.PLAYLIST:
        embed.add_field(name="即將播放", value="*無下一首，將重複播放此歌曲*", inline=False)
    
    elif len(playlist.order)-offset > 1:
        queuelist += f"**>> {playlist[1+offset].title}**\n*by {playlist[1+offset].requester}*\n"
        if len(playlist.order) > 2: 
            queuelist += f"*...還有 {len(playlist.order)-2-offset} 首歌*"

        embed.add_field(name=f"即將播放 | {len(playlist.order)-1-offset} 首歌待播中", value=queuelist, inline=False)

    if 'spotify' in playlist.current().uri:
        embed.set_thumbnail(url=playlist.current().cover)

    if playlist.current().audio_source == 'soundcloud':
        embed.add_field(name=f"{caution_emoji} | 自動歌曲推薦已暫時停用", value=f'此歌曲不支援自動歌曲推薦功能，請選取其他歌曲來使用此功能', inline=False)

    return embed