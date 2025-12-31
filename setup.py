from setuptools import setup, find_packages

setup(
    name="g1-record-replay",
    version="0.1.0",
    description="Record and replay motor trajectories for Unitree G1 robot",
    author="Sitaram",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.20.0",
        "h5py>=3.0.0",
        "pyyaml>=5.4.0",
        "rich>=10.0.0",
        "matplotlib>=3.0.0",
        # Note: unitree_sdk2_python must be installed separately
        # cd ../unitree_sdk2_python && uv pip install -e .
    ],
    dependency_links=[
        # Local path to unitree SDK
        "file:///../unitree_sdk2_python#egg=unitree_sdk2py",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "g1-calibrate=scripts.calibrate:main",
            "g1-record=scripts.record:main",
            "g1-replay=scripts.replay:main",
            "g1-visualize=scripts.visualize_episode:main",
        ],
    },
)

