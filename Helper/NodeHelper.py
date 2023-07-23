import os
import wavelink
from wavelink.ext import spotify
import bilibili_api as bilibili
import asyncio
import random

class NodeHelper:
    def __init__(self):
        TW_HOST = os.getenv('WAVELINK_TW_HOST')
        LOCAL_SEARCH_HOST_1 = os.getenv('WAVELINK_SEARCH_HOST_1')
        LOCAL_SEARCH_HOST_2 = os.getenv('WAVELINK_SEARCH_HOST_2')
        PORT = os.getenv('WAVELINK_PORT')
        SEARCH_PORT_1 = os.getenv('WAVELINK_SEARCH_PORT_1')
        SEARCH_PORT_2 = os.getenv('WAVELINK_SEARCH_PORT_2')
        PASSWORD = os.getenv('WAVELINK_PWD')
        SPOTIFY_ID = os.getenv('SPOTIFY_ID')
        SPOTIFY_SECRET = os.getenv('SPOTIFY_SECRET')
        SESSDATA = os.getenv('SESSDATA')
        BILI_JCT = os.getenv('BILI_JCT')
        BUVID3 = os.getenv('BUVID3')
        DEDEUSERID = os.getenv('DEDEUSERID')
        AC_TIME_VALUE = os.getenv('AC_TIME_VALUE')
        
        self._playlist.init_spotify(SPOTIFY_ID, SPOTIFY_SECRET)
        mainplayhost = wavelink.Node(
            id="TW_PlayBackNode",
            uri=f"http://{TW_HOST}:{PORT}",
            use_http=True,
            password=PASSWORD,
        )
        searchhost_1 = wavelink.Node(
            id="SearchNode_1",
            uri=f"http://{LOCAL_SEARCH_HOST_1}:{SEARCH_PORT_1}",
            use_http=True,
            password=PASSWORD,
        )
        searchhost_2 = wavelink.Node(
            id="SearchNode_2",
            uri=f"http://{LOCAL_SEARCH_HOST_2}:{SEARCH_PORT_2}",
            use_http=True,
            password=PASSWORD,
        )

        self._bilibilic = bilibili.Credential(
            sessdata=SESSDATA,
            bili_jct=BILI_JCT,
            buvid3=BUVID3,
            dedeuserid=DEDEUSERID,
            ac_time_value=AC_TIME_VALUE
        )
        
        valid = asyncio.run(self._bilibilic.check_valid())

        print(f"[BiliBili API] Cookie valid: {valid}")

        self._spotify = spotify.SpotifyClient(client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET)

        asyncio.run(
            wavelink.NodePool.connect(
                client=self.bot,
                nodes=[mainplayhost, searchhost_1, searchhost_2],
                spotify=self._spotify
            )
        )

    @property
    def TW_PlaybackNode(self) -> wavelink.Node:
        return wavelink.NodePool.get_node(id="TW_PlayBackNode")

    @property
    def SearchNode_1(self) -> wavelink.Node:
        return wavelink.NodePool.get_node(id="SearchNode_1")
    
    @property
    def SearchNode_2(self) -> wavelink.Node:
        return wavelink.NodePool.get_node(id="SearchNode_2")

    async def get_best_searchnode(self) -> wavelink.Node:
        searchnode_1 = self.SearchNode_1
        searchnode_2 = self.SearchNode_2
        
        # decide from the cpu usage
        node_1_stats = await searchnode_1._send(method="GET", path="stats")
        node_2_stats = await searchnode_2._send(method="GET", path="stats")

        node_1_avgload = (node_1_stats["cpu"]["systemLoad"] + node_1_stats["cpu"]["lavalinkLoad"]) / 2
        node_2_avgload = (node_2_stats["cpu"]["systemLoad"] + node_2_stats["cpu"]["lavalinkLoad"]) / 2

        if node_1_avgload > node_2_avgload:
            return searchnode_2
        elif node_1_avgload < node_2_avgload:
            return searchnode_1
        else:
            return random.choice([searchnode_1, searchnode_2])

node_helper = NodeHelper()