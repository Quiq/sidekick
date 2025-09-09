# Sidekick

Sidekick enhances your AI Studio experience by facilitating code editing in your editor of choice through bidirectional WebSocket synchronization.

## Overview

Sidekick is a minimal Python server that enables real-time code synchronization between the AI Studio web app and your local file system, allowing you to edit and inspect project code in your editor of choice.

## Installation

### Recommended Setup with Miniconda

We recommend using Miniconda to create a dedicated environment for Sidekick. This ensures clean dependency management and allows you to easily pull updates.

#### 1. Install Miniconda

If you don't have Miniconda installed, download it from [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)

#### 2. Create a Dedicated Environment

```bash
# Create a new conda environment for Sidekick
conda create -n sidekick python=3.13
conda activate sidekick
```

#### 3. Install Sidekick in Development Mode

```bash
# Clone the repository
git clone https://github.com/Quiq/sidekick.git
cd sidekick

# Install in development mode (recommended)
pip install -e .
```

### Alternative Installation (Not Recommended)

If you prefer not to use Miniconda:

```bash
# Clone the repository
git clone https://github.com/Quiq/sidekick.git
cd sidekick

# Install in development mode
pip install -e .
```

## Quick Start

### 1. Start the Sidekick Server

```bash
# Start with default settings
sidekick

# Custom  workspace
sidekick --workspace /path/to/workspace

# See all options
sidekick --help
```

Default settings:
- **Port**: 43001
- **Host**: localhost (127.0.0.1) - hardcoded for security
- **Workspace**: `~/aistudio`

### 2. Connect from AI Studio

In the Configuration Panel, go to Preferences sub-panel and toggle on 'Edit code with Sidekick'. Circle should go from red to green when conntected

### 3. Edit Locally

Open your workspace (`~/aistudio`) in your favorite editor/IDE

Changes you make locally will automatically sync back to AI Studio! In addition, edits made in the Function Editor
will be synced to your local disk

## File Structure

Sidekick organizes your projects in a clean directory structure:

```
~/aistudio/                    # Default workspace
└── projects/                  # All projects are nested under this directory
    ├── tenant1/               # Tenant: "tenant1"
    │   ├── project_alpha/     # Project: "project_alpha"
    │   │   └── functions.py   # Python code for this project
    │   └── my_ai_app/         # Project: "my_ai_app"
    │       └── functions.py   # Python code for this project
    └── tenant2/               # Tenant: "tenant2"
        └── experiment_123/    # Project: "experiment_123"
            └── functions.py   # Python code for this project
```
