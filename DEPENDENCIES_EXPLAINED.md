# Dependencies Explained

## Why is unitree_sdk2_python not in requirements.txt as a simple dependency?

Good question! Here's the full story:

### The Dependency Chain

```
g1-record-and-replay
  └── unitree_sdk2_python (local package, not on PyPI)
      └── cyclonedds==0.10.2 (needs to be compiled with C++)
          └── cyclonedds C library (must be installed separately)
```

### The Problem

1. **cyclonedds** is a C++ library that needs to be compiled
2. **unitree_sdk2_python** depends on the Python bindings for cyclonedds
3. **The Python cyclonedds package** (0.10.2) needs to find the compiled C library
4. **It's not a simple `pip install`** situation

### Why We Can't Just Do `pip install unitree_sdk2_python`

1. **Not on PyPI**: `unitree_sdk2_python` is distributed by Unitree as source code
2. **Local package**: It's located at `../unitree_sdk2_python`
3. **cyclonedds dependency**: Requires environment variable `CYCLONEDDS_HOME` to be set

### The Solution

We provide two installation methods:

#### Option 1: Automated Script (Recommended)
```bash
./setup_dependencies.sh
```

This handles everything including:
- Cloning and compiling cyclonedds
- Setting environment variables
- Installing unitree SDK
- Installing g1-record-and-replay
- Testing imports

#### Option 2: Manual (if you want control)
```bash
# 1. Build cyclonedds
cd ~
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir -p build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install

# 2. Set environment variable (add to ~/.bashrc)
export CYCLONEDDS_HOME="$HOME/cyclonedds/install"

# 3. Install unitree SDK
cd ~/projects/g1-piano/unitree_sdk2_python
uv pip install -e .

# 4. Install g1-record-and-replay
cd ~/projects/g1-piano/g1-record-and-replay
uv pip install -e .
```

### What's in requirements.txt?

```
numpy>=1.20.0           # Array operations
h5py>=3.0.0            # Episode storage (HDF5 format)
pyyaml>=5.4.0          # Config file reading
rich>=10.0.0           # Beautiful terminal UI
matplotlib>=3.0.0      # Trajectory visualization

-e ../unitree_sdk2_python  # Local path reference (requires cyclonedds)
```

The `-e ../unitree_sdk2_python` line tells pip/uv to install from the local path, but it still requires cyclonedds to be set up first.

### Why This Complexity?

This is common for robotics SDKs that:
- Use real-time communication (DDS/cyclonedds)
- Have C++ components for performance
- Need platform-specific compilation
- Aren't distributed through PyPI

### How to Check if Everything is Installed

```bash
# Activate venv
source .venv/bin/activate

# Test imports
python -c "import unitree_sdk2py; print('✓ SDK OK')"
python -c "from g1_record_replay.core import DataManager; print('✓ g1-record-and-replay OK')"
```

### Common Issues

#### Issue: "Could not locate cyclonedds"
**Cause:** CYCLONEDDS_HOME not set or cyclonedds not compiled  
**Fix:** Run `./setup_dependencies.sh` or set environment variable

#### Issue: "No module named 'unitree_sdk2py'"
**Cause:** unitree SDK not installed  
**Fix:** 
```bash
cd ../unitree_sdk2_python
CYCLONEDDS_HOME="$HOME/cyclonedds/install" uv pip install -e .
```

#### Issue: "NameError: name 'LowState_' is not defined"
**Cause:** Type hints failing when SDK not installed  
**Fix:** This is now handled with `TYPE_CHECKING` guards in the code

### The Bottom Line

**unitree_sdk2_python IS a dependency**, but it's a special kind that requires:
1. cyclonedds C library (compiled)
2. Environment variable set
3. Local path installation

We handle this with:
- Documentation (README, DEVELOPMENT.md, this file)
- Automated script (setup_dependencies.sh)
- Proper type hints that work even when SDK is not installed
- Clear error messages when SDK is missing

### For CI/CD

If you're setting up automated builds/testing:

```yaml
# Example GitHub Actions
- name: Install cyclonedds
  run: |
    git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
    cd cyclonedds && mkdir -p build install && cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=../install
    cmake --build . --target install
    echo "CYCLONEDDS_HOME=$HOME/cyclonedds/install" >> $GITHUB_ENV

- name: Install dependencies
  run: |
    cd unitree_sdk2_python && uv pip install -e .
    cd ../g1-record-and-replay && uv pip install -e .
```

## Summary

| Dependency | Type | Installation |
|------------|------|--------------|
| numpy, h5py, pyyaml, rich, matplotlib | PyPI packages | ✅ Auto-installed |
| cyclonedds C library | System library | ⚠️ Manual compile |
| unitree_sdk2_python | Local package | ⚠️ Requires cyclonedds |
| g1-record-and-replay | Local package | ✅ After above |

**Quick answer:** Run `./setup_dependencies.sh` and you're done! 🚀

