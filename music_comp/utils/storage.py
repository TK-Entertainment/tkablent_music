from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import *

import discord
import asyncio
import os
import atexit
import signal
import threading
import sonolink
from msgspec.json import decode as json_decode
from msgspec import DecodeError
from msgspec.json import encode as json_encode


class StorageBackend:
    """Process-wide in-memory mirror of music_comp/data.json with write-behind.

    The whole file is loaded once at startup (``warm()``) and then served from
    memory, so per-field reads never hit the disk on the event loop. Writes
    mutate the in-memory dict first (so reads are always consistent —
    read-your-writes) and persist asynchronously:

    * High-value, low-frequency keys (favorite, settings, text_channel, ...) are
      written through immediately (crash window matches the old behaviour).
    * Hot, low-stakes keys (recently_played, mostly_played) are coalesced with a
      short debounce, so e.g. song_played's two writes collapse to one disk pass.

    The flush encodes the full dict to bytes **on the loop** (msgspec is C and
    non-preemptible between awaits, so the worker thread never iterates a dict
    the loop can mutate — no torn write), then hands only the bytes to a thread
    for an atomic temp-file write + fsync + os.replace + .bak refresh. A
    loop-free ``flush_sync`` is registered via atexit + SIGTERM so pending writes
    survive a clean shutdown.

    This is the single source of truth: ``GuildInfo`` keeps no field state of its
    own, so the two representations can never diverge.
    """

    # Hot, low-stakes keys are debounced; everything else is write-through.
    _DEBOUNCED_KEYS = frozenset({"recently_played", "mostly_played"})
    _DEBOUNCE_SECONDS = 1.0

    def __init__(self):
        self._path: str = rf"{os.getcwd()}/music_comp/data.json"
        self._bak: str = self._path + ".bak"
        self._data = None  # the one in-memory copy of data.json

        self._dirty: bool = False
        self._immediate: bool = False
        self._started: bool = False
        self._loop = None
        self._task = None
        self._wake = asyncio.Event()
        self._lock = asyncio.Lock()

    # --- loading -------------------------------------------------------
    def _load_sync(self) -> dict:
        try:
            with open(self._path, "rb") as f:
                return json_decode(f.read())
        except DecodeError:
            # main file corrupted -> recover from the last-known-good backup
            with open(self._bak, "rb") as f:
                return json_decode(f.read())

    def _ensure_loaded(self) -> None:
        # Safety net if a read beats the startup warm(); normally a no-op.
        if self._data is None:
            self._data = self._load_sync()

    async def warm(self) -> None:
        """Load data.json into memory once, off the event loop. Idempotent."""
        if self._data is None:
            loaded = await asyncio.to_thread(self._load_sync)
            # Re-check: a read during the await may have populated it synchronously
            # via _ensure_loaded; don't overwrite (and lose) that copy.
            if self._data is None:
                self._data = loaded

    # --- startup -------------------------------------------------------
    def start(self, loop) -> None:
        """Launch the write-behind worker and register exit flushes. Idempotent."""
        if self._started:
            return
        self._started = True
        self._loop = loop
        self._task = loop.create_task(self._flush_worker())
        atexit.register(self._atexit_flush)
        # Persist pending writes on container stop (SIGTERM). Leave SIGINT to
        # discord.py / KeyboardInterrupt (atexit covers that graceful path).
        try:
            loop.add_signal_handler(signal.SIGTERM, self._on_sigterm)
        except (NotImplementedError, RuntimeError, ValueError):
            pass  # unsupported platform / not the main thread

    # --- reads ---------------------------------------------------------
    def get(self, guild_id: int, key: str):
        """Guild value if present, else the 'default' fallback (matches old fetch)."""
        self._ensure_loaded()
        guild = self._data.get(str(guild_id))
        if guild is None or guild.get(key) is None:
            return self._data["default"][key]
        return guild[key]

    def get_or_none(self, guild_id: int, key: str):
        """Guild value if present, else None (no default fallback) — for helper.fetch."""
        self._ensure_loaded()
        guild = self._data.get(str(guild_id))
        if guild is None or guild.get(key) is None:
            return None
        return guild[key]

    # --- writes --------------------------------------------------------
    def set(self, guild_id: int, key: str, value) -> None:
        self._ensure_loaded()
        gid = str(guild_id)
        if self._data.get(gid) is None:
            self._data[gid] = dict()
        self._data[gid][key] = value
        self._dirty = True

        if not self._started:
            # Worker not up yet (writes during startup): persist synchronously so
            # nothing is lost.
            self._write_now_sync()
            return

        if key not in self._DEBOUNCED_KEYS:
            self._immediate = True
        self._wake.set()

    async def _flush_worker(self) -> None:
        while True:
            await self._wake.wait()
            self._wake.clear()
            if not self._immediate:
                # coalesce a burst of hot writes into a single disk pass
                await asyncio.sleep(self._DEBOUNCE_SECONDS)
            self._immediate = False
            if self._dirty:
                await self._flush()

    async def _flush(self) -> None:
        async with self._lock:  # serialize os.replace publishes
            if not self._dirty:
                return
            self._dirty = False
            # Encode ON THE LOOP (non-preemptible between awaits) so the worker
            # thread never reads a structure the loop can mutate -> no torn write.
            data_bytes = json_encode(self._data)
        await asyncio.to_thread(self._write_bytes, data_bytes)

    # --- low-level durable write --------------------------------------
    def _write_bytes(self, data_bytes: bytes) -> None:
        # Unique temp name per writer thread so a concurrent loop-side
        # flush_sync (e.g. on SIGTERM) can never collide on the temp file.
        tmp = f"{self._path}.{os.getpid()}.{threading.get_ident()}.tmp"
        with open(tmp, "wb") as f:
            f.write(data_bytes)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self._path)  # atomic publish
        try:  # refresh the last-known-good backup (best-effort)
            with open(self._bak, "wb") as f:
                f.write(data_bytes)
                f.flush()
                os.fsync(f.fileno())
        except OSError:
            pass

    def _write_now_sync(self) -> None:
        self._dirty = False
        self._write_bytes(json_encode(self._data))

    # --- exit hooks ----------------------------------------------------
    def flush_sync(self) -> None:
        """Loop-free synchronous flush for process exit (atexit / signal)."""
        if self._data is None or not self._dirty:
            return
        self._write_now_sync()

    def _atexit_flush(self) -> None:
        try:
            self.flush_sync()
        except Exception:
            pass

    def _on_sigterm(self) -> None:
        # Persist pending writes, then restore the default disposition and
        # re-raise SIGTERM so the process terminates normally. (Avoids stopping
        # the loop out from under discord.py's asyncio.run / run_until_complete.)
        try:
            self.flush_sync()
        finally:
            if self._loop is not None:
                try:
                    self._loop.remove_signal_handler(signal.SIGTERM)
                except (NotImplementedError, RuntimeError, ValueError):
                    pass
            signal.raise_signal(signal.SIGTERM)


# Module-level singleton: one in-memory mirror shared by every guild's GuildInfo.
STORAGE = StorageBackend()


class GuildInfo:
    """Per-guild persistent settings, backed by the in-memory ``STORAGE``.

    Every getter reads from the single in-memory data.json mirror and every
    setter writes through it, so there is exactly one source of truth and the
    blocking full-file read is kept off the hot path (reads are served from
    memory after the startup ``warm()``).
    """

    def __init__(self, guild_id):
        self.guild_id: int = guild_id
        self._task: asyncio.Task = None

    @property
    def text_channel(self):
        return STORAGE.get(self.guild_id, "text_channel")

    @text_channel.setter
    def text_channel(self, value: int):
        STORAGE.set(self.guild_id, "text_channel", value)

    @property
    def recently_played(self):
        return STORAGE.get(self.guild_id, "recently_played")

    @recently_played.setter
    def recently_played(self, value: list):
        STORAGE.set(self.guild_id, "recently_played", value)

    @property
    def mostly_played(self):
        return sorted(
            STORAGE.get(self.guild_id, "mostly_played").items(),
            key=lambda item: item[1],
            reverse=True,
        )

    @mostly_played.setter
    def mostly_played(self, value: dict):
        STORAGE.set(self.guild_id, "mostly_played", value)

    def song_played(self, song: sonolink.models.Playable):
        if song.source_name == "http":
            identifier = song.extras.identifier
        else:
            identifier = song.identifier

        # Copy before mutating: STORAGE.get may return the shared "default"
        # object when this guild has no own entry yet, and mutating it in place
        # would corrupt the default / leak across guilds. set() then stores the
        # copy under this guild's key.
        recently_played = list(STORAGE.get(self.guild_id, "recently_played"))
        mostly_played = dict(STORAGE.get(self.guild_id, "mostly_played"))

        # Update the recently played list
        if identifier in recently_played:
            recently_played.remove(identifier)
        recently_played.insert(0, identifier)
        while len(recently_played) > 5:
            recently_played.pop()

        if song.extras.requester_id is not None:
            mostly_played[identifier] = mostly_played.get(identifier, 0) + 1

        STORAGE.set(self.guild_id, "recently_played", recently_played)
        STORAGE.set(self.guild_id, "mostly_played", mostly_played)

    @property
    def multitype_remembered(self):
        return STORAGE.get(self.guild_id, "multitype_remembered")

    @multitype_remembered.setter
    def multitype_remembered(self, value: bool):
        STORAGE.set(self.guild_id, "multitype_remembered", value)

    @property
    def multitype_choice(self):
        return STORAGE.get(self.guild_id, "multitype_choice")

    @multitype_choice.setter
    def multitype_choice(self, value: str):
        STORAGE.set(self.guild_id, "multitype_choice", value)

    @property
    def changelogs_latestversion(self):
        return STORAGE.get(self.guild_id, "changelogs_latestversion")

    @changelogs_latestversion.setter
    def changelogs_latestversion(self, value: str):
        STORAGE.set(self.guild_id, "changelogs_latestversion", value)

    @property
    def favorite(self):
        return STORAGE.get(self.guild_id, "favorite")

    def add_favorite(self, song: sonolink.models.Playable):
        if song.source_name == "http":
            identifier = song.extras.identifier
        else:
            identifier = song.identifier

        favorite = list(STORAGE.get(self.guild_id, "favorite"))
        if identifier not in favorite:
            favorite.append(identifier)
            STORAGE.set(self.guild_id, "favorite", favorite)

    def remove_favorite(self, song: sonolink.models.Playable):
        if song.source_name == "http":
            identifier = song.extras.identifier
        else:
            identifier = song.identifier

        favorite = list(STORAGE.get(self.guild_id, "favorite"))
        if identifier in favorite:
            favorite.remove(identifier)
            STORAGE.set(self.guild_id, "favorite", favorite)


class GuildUIInfo:
    def __init__(self, guild_id):
        self.guild_id: int = guild_id

        # Booleans
        # Determine whether auto stage modification available in this server
        # Currently deprecated
        self.auto_stage_available: bool = True
        # Stage topic existance
        # Bot won't start another stage instance if this is True
        self.stage_topic_exist: bool = False
        # Stage topic checking
        # True if bot already checked the topic
        self.stage_topic_checked: bool = False
        # Indicate the bot has skip the song
        # Will be reseted to False after next song played
        self.skip: bool = False
        # Indicate the last song is skipped or not
        self.lastskip: bool = False
        self.search: bool = False
        self.leaveoperation: bool = False
        self.music_suggestion: bool = False
        # Indicate that the suggestion is under processing
        # Will be reseted to False after process is done
        self.suggestion_processing: bool = False
        self.suggestion_failure: bool = False

        self.lasterrorinfo: dict = {}

        self.playinfo: Coroutine[Any, Any, discord.Message] = None
        self.playinfo_view: discord.ui.View = None
        self.processing_msg: discord.Message = None
        self.searchmsg: Coroutine[Any, Any, discord.Message] = None

        self.suggestions_source = None
        self.previous_titles: list[str] = []
        self.suggestions: list = []

        self.timer_task: asyncio.Task = None
