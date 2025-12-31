# Development Guide

## Environment Setup

This project uses **`uv`** for fast Python package management.

### Creating Virtual Environment
```bash
uv venv .venv
```

### Installing Dependencies

**⚠️ IMPORTANT: Always use `uv pip` instead of `pip`**

```bash
# Activate virtual environment
source .venv/bin/activate

# Install project in development mode
uv pip install -e .

# Install from requirements
uv pip install -r requirements.txt

# Install additional packages
uv pip install <package-name>
```

### Why `uv pip`?
- Much faster than standard pip
- Better dependency resolution
- Optimized for the uv ecosystem
- Consistent with project setup

## Development Workflow

### 1. Initial Setup
```bash
# Create and activate virtual environment
cd /home/sitaram/projects/g1-piano/g1-record-and-replay
uv venv .venv
source .venv/bin/activate

# Install unitree SDK first (required dependency)
cd ../unitree_sdk2_python
uv pip install -e .

# Install g1-record-and-replay
cd ../g1-record-and-replay
uv pip install -e .
```

### 2. Running Tests
```bash
source .venv/bin/activate
python tests/test_connection.py --network-interface eth0
```

### 3. Running Scripts
```bash
source .venv/bin/activate
python scripts/calibrate.py --network-interface eth0 --joint-group arms
python scripts/record.py --network-interface eth0 --name "test"
python scripts/replay.py --network-interface eth0 --episode data/episodes/episode_001.h5
```

### 4. Code Checking
```bash
# Check for import errors
python -m py_compile g1_record_replay/**/*.py

# Check syntax
python -c "import g1_record_replay; print('OK')"
```

## Project Structure
```
g1-record-and-replay/
├── .venv/                      # Virtual environment (created by uv)
├── g1_record_replay/           # Main package
│   ├── core/                   # Core functionality
│   │   ├── g1_interface.py    # Robot interface
│   │   └── data_manager.py    # Data storage
│   ├── calibrate.py           # Calibration logic
│   ├── record.py              # Recording logic
│   └── replay.py              # Replay logic
├── scripts/                    # CLI entry points
├── tests/                      # Tests
├── config/                     # Configuration
└── data/                       # Episode storage
```

## Dependencies

### Core Dependencies (from requirements.txt)
- `numpy>=1.20.0` - Array operations
- `h5py>=3.0.0` - Episode storage
- `pyyaml>=5.4.0` - Config files
- `rich>=10.0.0` - Terminal UI
- `matplotlib>=3.0.0` - Visualization

### External Dependencies (REQUIRED - install first!)
- `unitree_sdk2_python` - Robot SDK (located at `../unitree_sdk2_python`)
  ```bash
  # Must be installed before g1-record-and-replay
  cd ../unitree_sdk2_python
  uv pip install -e .
  ```
  
  This provides the core SDK for communicating with the G1 robot.

## Common Issues

### Issue: Command 'pip' not found
**Solution:** Use `uv pip` instead of `pip`

### Issue: Module not found
**Solution:** Make sure venv is activated and package is installed
```bash
source .venv/bin/activate
uv pip install -e .
```

### Issue: unitree_sdk2py not found
**Solution:** Install the SDK separately
```bash
cd ~/projects/g1-piano/unitree_sdk2_python
uv pip install -e .
```

## Best Practices

1. **Always activate venv before running commands**
   ```bash
   source .venv/bin/activate
   ```

2. **Use `uv pip` for all package operations**
   - ✅ `uv pip install numpy`
   - ❌ `pip install numpy`

3. **Install in editable mode for development**
   ```bash
   uv pip install -e .
   ```

4. **Keep requirements.txt updated**
   ```bash
   uv pip freeze > requirements.txt
   ```

## Quick Reference

```bash
# Setup
uv venv .venv
source .venv/bin/activate
uv pip install -e .

# Test
python tests/test_connection.py --network-interface eth0

# Calibrate
python scripts/calibrate.py --network-interface eth0

# Record
python scripts/record.py --network-interface eth0 --name "my_motion"

# Replay
python scripts/replay.py --network-interface eth0 --episode data/episodes/<file>.h5

# Visualize
python scripts/visualize_episode.py --list
python scripts/visualize_episode.py --episode data/episodes/<file>.h5
```

