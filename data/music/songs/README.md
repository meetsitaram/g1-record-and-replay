# Song Files

This directory contains example song files for the G1 Music Feature.

## Available Songs

### Beginner
- **c_major_scale.txt** - Simple C major scale, good for testing single notes
- **mary_had_lamb.txt** - Classic nursery rhyme, right hand only

### Intermediate
- **twinkle_star.txt** - Full lullaby with rests, left hand only
- **two_hand_demo.txt** - Demonstrates simultaneous left/right hand playing

## Song File Format

```text
# Comments start with hash
# Blank lines are ignored

# Each line is a musical phrase
note:hand:duration -> note:hand:duration -> note:hand:duration

# Use ';' for simultaneous notes (chords)
C1:left:full;E1:right:full

# Use 'rest' for pauses
rest:none:quarter
```

## Creating Your Own Songs

1. Choose your notes and map to hands
2. Determine durations (quarter, half, full, etc.)
3. Create a `.txt` file in this directory
4. Test with `--dry-run` first:
   ```bash
   python scripts/music/play_music.py --instrument piano \
       --song-file data/music/songs/your_song.txt --dry-run
   ```

## Duration Reference

At 120 BPM (default):
- **full** (whole note): 2.0 seconds
- **half** (half note): 1.0 seconds
- **quarter** (quarter note): 0.5 seconds
- **eighth** (eighth note): 0.25 seconds
- **sixteenth** (sixteenth note): 0.125 seconds

## Tips

- Start with simple melodies
- Keep episodes short (0.3-1.0s per note)
- Use rests for musical phrasing
- Test individual notes before full songs
- Adjust tempo with `--tempo-multiplier` if needed

