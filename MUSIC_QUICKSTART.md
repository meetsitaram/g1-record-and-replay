# G1 Music Feature - Quick Start

Get your G1 robot playing music in 4 easy steps!

## 🆕 New Features
- 🔊 **Audio Prompts**: Text-to-speech announces each step (hands-free!)
- 🔍 **Dry Run Mode**: Test workflow without robot connection
- ⚖️ **Smart Trimming**: Weighted thresholds prioritize shoulder positioning
- 👁️ **Visual Preview**: Safely preview trimmed episodes with manual positioning

## Step 1: Setup Configuration (5 minutes)

```bash
python scripts/music/setup_music_config.py
```

Follow the prompts:
- Instrument name: `piano`
- Description: `My piano`
- Tempo: `120` (default)
- Time signature: `4/4` (default)
- Add notes: Configure at least 4-5 notes (e.g., C1, D1, E1, F1, G1)

Or use the template:
```bash
python scripts/music/setup_music_config.py --batch-file data/music/configs/notes_template.csv
```

## Step 2: Record Episodes (15-30 minutes)

### 🔍 Option A: Dry Run First (No Robot Needed)

Test the workflow without hardware:
```bash
python scripts/music/record_music.py --instrument piano --dry-run
```

This simulates the entire recording process so you understand what to expect!

### 🤖 Option B: Record with Robot

**Important Setup:**
1. Position G1 sitting on a chair
2. Clear space around the piano/instrument
3. Have someone ready to physically guide the robot's arms

```bash
# With audio prompts (recommended - hands-free!)
python scripts/music/record_music.py --instrument piano

# Silent mode (no audio)
python scripts/music/record_music.py --instrument piano --no-audio
```

**🔊 With Audio Prompts:** The system will announce each note (e.g., "Recording note C1, left hand") so you can focus on guiding the robot without looking at the screen!

For each note:
1. 🔊 *Hear the note name announced*
2. Position hand above the key
3. 🔊 *"Ready to record. Press enter to start"*
4. Press the key smoothly
5. Press 'S' to stop recording

## Step 3: Test Individual Notes

```bash
# Validate a sequence without playing
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter" --dry-run

# Play a single note (SAFELY!)
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter"
```

## Step 4: Play a Song!

```bash
# Play a simple scale
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter -> D1:left:quarter -> E1:left:quarter -> F1:left:quarter -> G1:left:quarter"

# Or use a pre-made song file
python scripts/music/play_music.py --instrument piano \
    --song-file data/music/songs/mary_had_lamb.txt
```

## Quick Commands Reference

### Recording
```bash
# Dry run (no robot needed - test workflow)
python scripts/music/record_music.py --instrument piano --dry-run

# Check recording status
python scripts/music/record_music.py --instrument piano --list-status

# Record specific notes only
python scripts/music/record_music.py --instrument piano --notes C1,D1,E1

# Record without audio prompts
python scripts/music/record_music.py --instrument piano --no-audio
```

### Trimming Episodes
```bash
# Trim by frame count
python scripts/music/trim_episode.py --instrument piano --note C1 \
    --trim-start 5 --trim-end 3

# Trim by time (first 100ms and last 200ms)
python scripts/music/trim_episode.py --instrument piano --note C1 \
    --start-time 0.1 --end-time 0.8

# Preview trimming (text only - safe)
python scripts/music/trim_episode.py --instrument piano --note C1 \
    --start-time 0.1 --preview

# Visual preview with robot (manually position first - safest!)
python scripts/music/trim_episode.py --instrument piano --note C1 \
    --start-time 0.1 --visual-preview --interface eth0
```

### Playing Music
```bash
# Validate sequence without playing
python scripts/music/play_music.py --instrument piano \
    --sequence "..." --dry-run

# Play slower (half speed tempo)
python scripts/music/play_music.py --instrument piano \
    --sequence "..." --tempo-multiplier 0.5

# Play with faster motor movement
python scripts/music/play_music.py --instrument piano \
    --sequence "..." --speed 1.5
```

## Sequence Format Cheat Sheet

```bash
# Single note
"C1:left:quarter"

# Multiple notes in sequence (use ->)
"C1:left:quarter -> D1:left:quarter -> E1:left:half"

# Simultaneous notes / chord (use ;)
"C1:left:full;C2:right:full"

# Rest / pause
"rest:none:quarter"

# Complete example
"C1:left:quarter -> D1:left:quarter -> rest:none:quarter -> E1:left:half"
```

## Common Durations

At 120 BPM:
- `full` = 2.0s (whole note)
- `half` = 1.0s (half note)
- `quarter` = 0.5s (quarter note)
- `eighth` = 0.25s (eighth note)

## Troubleshooting

**"Episode not found"**
- Check: `python scripts/music/record_music.py --instrument piano --list-status`
- Record missing note: `python scripts/music/record_music.py --instrument piano --notes C1`

**"Hand mismatch"**
- Note is configured for different hand
- Check config: `python scripts/music/play_music.py --instrument piano --show-config`

**Robot moves too fast**
- Use `--tempo-multiplier 0.5` to slow down

**Robot moves too slow**
- Use `--tempo-multiplier 1.5` or `--speed 1.5`

**Want to test without robot?**
- Use `--dry-run` for recording: See the full workflow simulated
- Use `--dry-run` for playback: Validate sequences without movement

**Need to trim episodes?**
- Text preview first: `--preview` (safe, no movement)
- Visual preview: `--visual-preview --interface eth0` (manually position arms first!)

**Audio prompts not working?**
- macOS: Should work out of box (uses `say`)
- Linux: Install `espeak`: `sudo apt-get install espeak`
- Disable: Use `--no-audio` flag

## Safety Reminders

⚠️ **ALWAYS:**
- Clear area around robot
- Supervise during playback
- Use `--dry-run` first for new sequences
- Have emergency stop ready (Ctrl+C)

## 🎯 Pro Tips

### Recording
- **Use audio prompts** - Keep hands free to guide robot arms
- **Start with dry run** - Understand workflow before using robot
- **Record in quiet environment** - Audio prompts work best without noise
- **Test with fewer notes first** - Record 2-3 notes to verify process

### Trimming
- **Text preview always first** - Use `--preview` before any trimming
- **Trim by time, not frames** - Use `--start-time 0.1` (more intuitive)
- **Visual preview for verification** - Manually position arms, system checks distance
- **Focus on shoulders** - ⭐⭐⭐ Critical! System weights these most heavily
- **Wrists can vary** - ⭐ Less critical, more tolerance allowed

### Playback
- **Dry run sequences first** - Validate before robot moves
- **Start slow** - Use `--tempo-multiplier 0.5` for first playback
- **Test single notes** - Before playing full songs
- **Clear space** - Always ensure area around robot is clear

## 🆕 Feature Highlights

### Audio Prompts (Hands-Free Operation)
System announces: "Recording note C1, left hand" → You focus on robot, not screen!

### Smart Trimming (Weighted Thresholds)
- Shoulders: Must be within ~16° (most critical - moves entire arm)
- Elbows: Within ~24° (high importance - moves forearm)
- Wrists: Within ~28° (moderate - only moves hand)
- Fingers: Within ~57° (low importance - very localized)

### Visual Preview (Manual Positioning)
1. System shows target positions with importance stars (⭐⭐⭐)
2. Sets motors passive - YOU move arms manually
3. System checks distance and warns if too far
4. Minimal automatic transition to exact position
5. Plays episode, asks to save if good

## Next Steps

1. 📖 Read the full guide: `MUSIC_FEATURE_GUIDE.md`
2. 🎼 Create your own songs in `data/music/songs/`
3. 🎹 Experiment with different instruments
4. 🤝 Share your songs with the community!
5. 💡 Check `MUSIC_IMPLEMENTATION_SUMMARY.md` for technical details

## Example: Complete Workflow

### Workflow with Dry Run (Recommended for First Time)

```bash
# 1. Setup configuration
python scripts/music/setup_music_config.py --instrument piano
# Configure notes: C1, D1, E1, F1, G1 (left hand)

# 2. Test workflow without robot (dry run)
python scripts/music/record_music.py --instrument piano --dry-run
# Understand the full recording process, ~1 minute

# 3. Record with robot (when ready)
python scripts/music/record_music.py --instrument piano
# Audio prompts guide you through each step

# 4. Verify recordings
python scripts/music/record_music.py --instrument piano --list-status

# 5. Trim if needed (preview first)
python scripts/music/trim_episode.py --instrument piano --note C1 \
    --start-time 0.1 --preview

# 6. Apply trimming
python scripts/music/trim_episode.py --instrument piano --note C1 \
    --start-time 0.1

# 7. Test single note (validate only)
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter" --dry-run

# 8. Play single note (real playback)
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter"

# 9. Play full scale
python scripts/music/play_music.py --instrument piano \
    --sequence "C1:left:quarter -> D1:left:quarter -> E1:left:quarter -> F1:left:quarter -> G1:left:quarter"
```

### Visual Preview Workflow (Advanced)

```bash
# 1. Load trimmed episode for preview
python scripts/music/trim_episode.py --instrument piano --note C1 \
    --start-time 0.1 --visual-preview --interface eth0

# What happens:
#   → Shows target joint positions (⭐⭐⭐ = focus on shoulders!)
#   → Sets motors to passive mode
#   → You manually position arms close to target
#   → System checks distance (Green ✓ if close)
#   → Small smooth transition to exact position
#   → Plays trimmed episode
#   → Asks if you want to save

# 2. If motion looks good, save the trimmed episode
#    (prompted automatically after preview)
```

Happy music making! 🎵🤖

