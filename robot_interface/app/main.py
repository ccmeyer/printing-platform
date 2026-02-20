from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from .adapters.legacy_platform import LegacyConfig, LegacyPlatformAdapter
from .adapters.mock import MockRobotAdapter
from .controller import RobotController
from .models import (
    ConnectRequest,
    MoveToWellRequest,
    MoveXYZRequest,
    PrintDropletsRequest,
    RobotStatus,
    SetPressureRequest,
)

app = FastAPI(title="Dobbie Robot Control API", version="0.1.0")


def _build_adapter():
    adapter_mode = os.getenv("DOBBIE_ADAPTER", "mock").strip().lower()
    if adapter_mode != "legacy":
        return MockRobotAdapter()

    default_root = Path(
        r"C:\Users\aless\OneDrive - University of California, Davis\printing_platform\printing-platform"
    )
    root = Path(os.getenv("DOBBIE_PRINTING_PLATFORM_ROOT", str(default_root)))
    settings = Path(
        os.getenv(
            "DOBBIE_PRINTING_PLATFORM_SETTINGS",
            str(root / "Scripts" / "default_settings.json"),
        )
    )
    return LegacyPlatformAdapter(
        LegacyConfig(
            printing_platform_root=root,
            settings_path=settings,
            dobot_port_override=os.getenv("DOBBIE_DOBOT_PORT"),
            arduino_port_override=os.getenv("DOBBIE_ARDUINO_PORT"),
        )
    )


controller = RobotController(adapter=_build_adapter())


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/status", response_model=RobotStatus)
def status() -> RobotStatus:
    return controller.status()


@app.post("/connect", response_model=RobotStatus)
def connect(req: ConnectRequest) -> RobotStatus:
    try:
        controller.connect(simulation=req.simulation)
        return controller.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/disconnect", response_model=RobotStatus)
def disconnect() -> RobotStatus:
    try:
        controller.disconnect()
        return controller.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/robot/home", response_model=RobotStatus)
def robot_home() -> RobotStatus:
    try:
        controller.home()
        return controller.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/robot/move_xyz", response_model=RobotStatus)
def robot_move_xyz(req: MoveXYZRequest) -> RobotStatus:
    try:
        controller.move_xyz(req.x, req.y, req.z)
        return controller.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/robot/move_to_well", response_model=RobotStatus)
def robot_move_to_well(req: MoveToWellRequest) -> RobotStatus:
    try:
        controller.move_to_well(req.row, req.column)
        return controller.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/pressure/set", response_model=RobotStatus)
def pressure_set(req: SetPressureRequest) -> RobotStatus:
    try:
        controller.set_pressure(req.pulse, req.refuel, req.runtime)
        return controller.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/print/droplets", response_model=RobotStatus)
def print_droplets(req: PrintDropletsRequest) -> RobotStatus:
    try:
        controller.print_droplets(
            req.count, req.frequency, req.pulse_width, req.refuel_width
        )
        return controller.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/emergency_stop", response_model=RobotStatus)
def emergency_stop() -> RobotStatus:
    try:
        controller.emergency_stop()
        return controller.status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
