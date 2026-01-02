"""Music Module - Teach G1 to play musical instruments"""

from .music_config import MusicConfig
from .music_recorder import MusicRecorder
from .episode_trimmer import EpisodeTrimmer
from .music_replayer import MusicReplayer, NoteAction, ChordAction

__all__ = [
    'MusicConfig',
    'MusicRecorder',
    'EpisodeTrimmer',
    'MusicReplayer',
    'NoteAction',
    'ChordAction'
]

