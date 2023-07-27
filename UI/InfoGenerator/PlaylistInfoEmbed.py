import discord
import wavelink
from typing import *

from Misc.Enums import SpotifyAlbum, SpotifyPlaylist

from UI.Generic.Emojis import Emoji
from UI.Generic.Enums import Language, UIModule
from UI.Generic.Essentials import essentials

class PlaylistInfoEmbed(discord.Embed):
    def __init__(self, playlist: Union[SpotifyAlbum, wavelink.YouTubePlaylist], requester: discord.User, lang: Language):
        # Generate Embed Body
        strings = essentials.get_language_dict(lang, UIModule.InfoGenerator)
        
        if isinstance(playlist, list):
            title = "{} | {}" \
                    .format(Emoji.Search, strings["PlaylistInfo.BySearch"])
            url = None
        elif isinstance(playlist, wavelink.YouTubePlaylist):
            title = ":newspaper: | {}".format(strings["PlaylistInfo.ByYTPlaylist"])
            url = None
        else:
            title = f"{Emoji.Search} | {playlist.name}"
            url = playlist.uri

        color = discord.Colour.from_rgb(97, 219, 83)

        super().__init__(title=title, url=url, colour=color)

        if requester.discriminator == "0":
            string = strings["PlaylistInfo.Source.New"] \
                        .replace(r"{name}", requester.name)
        else:
            string = strings["PlaylistInfo.Source.Old"] \
                        .replace(r"{name}", requester.name) \
                        .replace(r"{code}", requester.discriminator)
        self.set_author(name=string, icon_url=requester.display_avatar)

        pllist: str = ""
        if isinstance(playlist, list):
            tracklist = playlist
        else:
            tracklist = playlist.tracks
        for i, track in enumerate(tracklist):
            pllist += f"{i+1}. {track.title}\n"
            if i == 1: 
                break
        if len(tracklist) > 2:
            pllist += strings["Info.Upcoming.Count"].replace(r"{count}", len(tracklist)-2)
        
        self.add_field(
            name=strings["PlaylistInfo.SubTitle"].replace(r"{count}", len(tracklist)),
            value=pllist, 
            inline=False)
        
        if isinstance(playlist, Union[SpotifyPlaylist, SpotifyAlbum]):
            self.set_thumbnail(url=playlist.thumbnail)
        
        embed_opt = essentials.embed_opt()
        self._footer = embed_opt