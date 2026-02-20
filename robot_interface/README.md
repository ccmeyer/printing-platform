# Dobbie Robot Interface (Phase 0 Skeleton)

This folder contains the first version of a remote robot-control service.

Goal:
- Run this service on the robot computer (the one connected to Dobot/Arduino/regulator/scale).
- Call it from your existing Streamlit app on another computer.

Current status:
- Safe mock mode is implemented for UI/API testing without hardware.
- Legacy hardware adapter is included and opt-in via environment variable.

## Why this architecture

Your hardware is on a different computer, so direct COM/USB calls from this app machine will not work.
The robot computer must host a control service, and your app should call it over the network.

## Quick start (mock mode)

1. Create an environment on the robot PC (or any test PC) and install:
   - `pip install -r robot_interface/requirements.txt`
2. From `Dobbie_app`, run:

```powershell
python -m uvicorn robot_interface.app.main:app --host 0.0.0.0 --port 8765
```

3. Check:
   - `http://<robot-pc-ip>:8765/health`
   - `http://<robot-pc-ip>:8765/docs`

## Legacy hardware mode (robot PC)

This mode wraps your existing `printing-platform` modules without modifying them.

Set environment variables before starting:

```powershell
$env:DOBBIE_ADAPTER="legacy"
$env:DOBBIE_PRINTING_PLATFORM_ROOT="C:\Users\aless\OneDrive - University of California, Davis\printing_platform\printing-platform"
# Optional explicit settings file:
# $env:DOBBIE_PRINTING_PLATFORM_SETTINGS="C:\...\printing-platform\Scripts\default_settings.json"
# Optional COM overrides:
# $env:DOBBIE_DOBOT_PORT="COM3"
# $env:DOBBIE_ARDUINO_PORT="COM6"

python -m uvicorn robot_interface.app.main:app --host 0.0.0.0 --port 8765
```

Notes:
- If defaults (ports/calibration files) are wrong, adapter raises a clear error instead of opening an interactive prompt.
- Original `printing-platform` code remains untouched.

## API summary

- `GET /health`
- `GET /status`
- `POST /connect`
- `POST /disconnect`
- `POST /robot/home`
- `POST /robot/move_xyz`
- `POST /robot/move_to_well`
- `POST /pressure/set`
- `POST /print/droplets`
- `POST /emergency_stop`

## Next step: hardware adapter

Implement `LegacyPlatformAdapter` in `robot_interface/app/adapters/legacy_platform.py`:
- import and wrap your existing `Scripts/print_platform_API.py` functionality
- remove keyboard/input blocking behavior from invoked methods
- provide deterministic status and error handling

Then switch adapter choice in `robot_interface/app/main.py`.
