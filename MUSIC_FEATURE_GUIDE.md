# G1 Music Feature Guide

## Overview

The G1 Music Feature enables the Unitree G1 humanoid robot to learn and play musical instruments by recording individual notes and replaying them in sequences to perform songs.

## Key Concepts

### Note Structure
Each note in a sequence has three components:
- **Note Name**: The musical note (e.g., `C1`, `D2`, `E3`)
- **Hand**: Which hand plays it (`left` or `right`)
- **Duration**: How long to wait after playing (`full`, `half`, `quarter`, `eighth`, `sixteenth`)

Format: `note:hand:duration`

Example: `C1:left:quarter`

### Sequence Format
- `->` separates sequential notes (play one after another)
- `;` separates simultaneous notes (play together as a chord)
- `rest:none:duration` creates a pause

Examples:
```
# Simple melody
C1:left:quarter -> D1:left:quarter -> E1:left:half

# Chord (simultaneous notes)
C1:left:full;E1:right:full;G1:right:full

# With rests
C1:left:quarter -> rest:none:quarter -> D1:left:quarter
```

### Note Durations
Durations are calculated based on tempo (BPM):
- **full**: Whole note (4 beats)
- **half**: Half note (2 beats)
- **quarter**: Quarter note (1 beat)
- **eighth**: Eighth note (0.5 beats)
- **sixteenth**: Sixteenth note (0.25 beats)

At 120 BPM (default), 1 beat = 0.5 seconds.

## Workflow

### 1. Setup Instrument Configuration

Create a configuration for your instrument:

```bash
python scripts/music/setup_music_config.py
```

Interactive prompts will guide you through:
- Instrument name (e.g., "piano", "drums")
- Description
- Tempo (BPM)
- Time signature
- Notes to configure (name + hand)

Or use batch mode with a CSV file:
```bash
python scripts/music/setup_music_config.py --batch-file notes.csv
```

CSV format:
```csv
C1,left
D1,left
E1,left
C2,right
D2,right
```

### 2. Record Episodes

Record episodes for all configured notes:

```bash
python scripts/music/record_music.py --instrument piano
```

This will:
1. Record initial position (sitting with arms ready)
2. Record each note (right hand first, then left hand)
3. Record final position (return to rest)

Options:
```bash
# Record specific notes only
python scripts/music/record_music.py --instrument piano --notes C1,D1,E1

# Skip init/final positions (if already recorded)
python scripts/music/record_music.py --instrument piano --skip-init --skip-final

# Check recording status
python scripts/music/record_music.py --instrument piano --list-status

# View note details
python scripts/music/record_music.py --instrument piano --note-details C1
```

### 3. Trim Episodes (Optional)

Trim unwanted frames from recorded episodes:

```bash
# Trim by frame count
python scripts/music/trim_episode.py --instrument piano --note C1 --trim-start 5 --trim-end 3

# Trim by time
python scripts/music/trim_episode.py --episode data/music/episodes/piano/C1_left.h5 \
    --start-time 0.1 --end-time 0.8

# Preview without saving
python scripts/music/trim_episode.py --instrument piano --note C1 --trim-start 5 --preview
```

The original episode is automatically backed up before modification.

### 4. Play Music

Play a musical sequence:

```bash
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter -> D1:left:quarter -> E1:left:half"
```

Or load from a song file:
```bash
python scripts/music/play_music.py --instrument piano --song-file data/music/songs/mary_had_lamb.txt
```

Options:
```bash
# Adjust playback speed (motor movement speed)
--speed 1.5

# Adjust tempo (timing between notes)
--tempo-multiplier 1.2

# Override tempo BPM
--override-bpm 140

# Skip position transitions
--skip-init --skip-final

# Validate without playing
--dry-run
```

## Song File Format

Create text files with your musical sequences:

```text
# Mary Had a Little Lamb
# Tempo: 120 BPM

# Verse 1
E2:right:quarter -> D2:right:quarter -> C2:right:quarter -> D2:right:quarter
E2:right:quarter -> E2:right:quarter -> E2:right:half

D2:right:quarter -> D2:right:quarter -> D2:right:half
E2:right:quarter -> G2:right:quarter -> G2:right:half

# Verse 2 with chords
E2:right:quarter;C1:left:quarter -> D2:right:quarter;B1:left:quarter
```

Lines starting with `#` are comments. Each non-comment line is a phrase/measure.

## Examples

### Example 1: Simple Scale
```bash
# Setup
python scripts/music/setup_music_config.py --instrument piano

# Configure notes: C1, D1, E1, F1, G1 (all left hand)

# Record
python scripts/music/record_music.py --instrument piano

# Play
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter -> D1:left:quarter -> E1:left:quarter -> F1:left:quarter -> G1:left:quarter"
```

### Example 2: Two-Hand Melody
```bash
# Sequence with both hands
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:half -> E2:right:half -> D1:left:quarter;D2:right:quarter"
```

### Example 3: Song with Rests
```bash
# Create song file
cat > data/music/songs/twinkle.txt << EOF
# Twinkle Twinkle Little Star
C1:left:quarter -> C1:left:quarter -> G1:left:quarter -> G1:left:quarter
A1:left:quarter -> A1:left:quarter -> G1:left:half
rest:none:quarter
F1:left:quarter -> F1:left:quarter -> E1:left:quarter -> E1:left:quarter
D1:left:quarter -> D1:left:quarter -> C1:left:half
EOF

# Play
python scripts/music/play_music.py --instrument piano --song-file data/music/songs/twinkle.txt
```

## Tips & Best Practices

### Recording Tips
1. **Positioning**: Start each note recording with the hand positioned just above the key/pad
2. **Consistency**: Try to maintain consistent speed and motion for each note
3. **Episode Length**: Keep note episodes short (0.3-1.0 seconds is ideal)
4. **Trim**: Use the trimmer to remove unnecessary frames at the start/end

### Playback Tips
1. **Start Slow**: Use `--tempo-multiplier 0.5` to practice slowly first
2. **Test Individual Notes**: Play single notes to verify they sound correct
3. **Dry Run**: Always use `--dry-run` first to validate sequences
4. **Safety**: Ensure clear space around the robot during playback

### Troubleshooting

**Episode not found error:**
```bash
# Check recording status
python scripts/music/record_music.py --instrument piano --list-status

# Re-record missing note
python scripts/music/record_music.py --instrument piano --notes C1
```

**Hand mismatch error:**
- The sequence specifies a different hand than configured
- Update your sequence or re-configure the note

**Duration validation error:**
- Check spelling of duration types
- Available: full, half, quarter, eighth, sixteenth

**Robot moves too fast/slow:**
- Adjust `--speed` for motor movement speed
- Adjust `--tempo-multiplier` for timing between notes

## Configuration Files

### Instrument Config Location
`data/music/configs/{instrument}.json`

### Episode Location
`data/music/episodes/{instrument}/`

Example structure:
```
data/music/episodes/piano/
├── init-position.h5
├── final-position.h5
├── C1_left.h5
├── D1_left.h5
├── C2_right.h5
└── D2_right.h5
```

## Advanced Features

### Custom Note Durations
Edit the configuration file to add custom durations:
```json
{
  "note_durations": {
    "full": 2.0,
    "half": 1.0,
    "quarter": 0.5,
    "triplet": 0.33
  }
}
```

### Tempo Changes
Change tempo dynamically:
```bash
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter -> D1:left:quarter" \
    --override-bpm 140
```

### Parallel Recording
Record multiple instruments:
```bash
# Setup piano
python scripts/music/setup_music_config.py --instrument piano

# Setup drums
python scripts/music/setup_music_config.py --instrument drums

# Record both
python scripts/music/record_music.py --instrument piano
python scripts/music/record_music.py --instrument drums
```

## Safety Considerations

1. **Clear Space**: Ensure adequate space around robot during playback
2. **Emergency Stop**: Press Ctrl+C to stop playback immediately
3. **Joint Limits**: Episodes are validated against joint limits
4. **Supervised Operation**: Always supervise the robot during music playback
5. **Start Position**: Ensure robot starts in safe sitting position

## API Usage

You can also use the music module programmatically:

```python
from g1_record_replay.music import MusicConfig, MusicReplayer
from g1_record_replay.core import G1Interface, DataManager

# Load configuration
config = MusicConfig.load("piano")

# Initialize
interface = G1Interface()
interface.initialize()
data_manager = DataManager()

# Create replayer
replayer = MusicReplayer(config, interface, data_manager)

# Play sequence
replayer.play_song("C1:left:quarter -> D1:left:quarter -> E1:left:half")

# Cleanup
interface.shutdown()
```

## Future Enhancements

Potential improvements:
- [ ] Visual note editor GUI
- [ ] MIDI file import
- [ ] Multi-instrument coordination
- [ ] Dynamic velocity (soft/loud)
- [ ] Pedal support (for piano)
- [ ] Real-time recording from MIDI keyboard

