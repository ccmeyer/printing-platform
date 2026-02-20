# Dobbie Robot UI Integration Plan

## Objective

Control Dobbie + peripherals from your app UI, while hardware remains on the robot computer.

## Architecture

1. Robot PC runs a control service (this FastAPI backend).
2. Service talks to hardware locally via COM/USB and vendor SDKs.
3. Your Streamlit app calls service endpoints over LAN.
4. Service enforces state, command serialization, logging, and emergency stop.

## Phased rollout

## Phase 0 (done in this commit)
- Create API skeleton and stateful controller.
- Add mock adapter to test UI and workflows without hardware.

## Phase 1 (next)
- Build `LegacyPlatformAdapter` around your existing platform code.
- Start with non-destructive operations:
  - connect/disconnect
  - status
  - home
  - move xyz
  - move_to_well
  - pressure set on/off
- Remove keyboard/input dependencies from the called execution path.

## Phase 2
- Add print operations:
  - print droplets
  - print array from selected CSV on robot PC
- Add operation queue and explicit job IDs.
- Add hard timeouts and recoverable error states.

## Phase 3
- Add Streamlit robot tab:
  - connection panel
  - jog controls
  - pressure controls
  - print actions
  - live status + logs
  - one-click emergency stop

## Safety requirements before real runs

- Every command path must be non-blocking or have timeout.
- Single-writer command lock (already in controller).
- Explicit `busy` state in UI and backend.
- `emergency_stop` endpoint tested physically.
- Coordinate limits and soft interlocks implemented.

## Network/deployment requirements

- Host backend on robot PC with fixed local IP.
- Open one firewall port (default `8765`) to lab subnet only.
- Configure API base URL in Streamlit (do not hard-code).
- Keep backend and hardware SDK versions pinned on robot PC.

## Immediate next coding step

Create `robot_interface/app/adapters/legacy_platform.py` and map it to:
- `Platform.initiate_all()`
- `Platform.disconnect_all()`
- `Platform.home_dobot()`
- `Platform.move_dobot(...)`
- `Platform.move_to_well(...)`
- `Platform.set_pressure(...)`
- `Platform.print_droplets(...)`

Then switch adapter instantiation in `robot_interface/app/main.py`.
