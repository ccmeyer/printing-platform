from __future__ import annotations

import time

from .base import RobotAdapter


class MockRobotAdapter(RobotAdapter):
    def __init__(self) -> None:
        self.connected = False
        self.simulation = True
        self.coords = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.row = 0
        self.column = 0
        self.pressure = {"pulse": 0.0, "refuel": 0.0}

    def connect(self, simulation: bool) -> None:
        self.simulation = simulation
        self.connected = True

    def disconnect(self) -> None:
        self.connected = False

    def home(self) -> None:
        self._ensure_connected()
        self.coords = {"x": 200.0, "y": 0.0, "z": 150.0}

    def move_xyz(self, x: float, y: float, z: float) -> None:
        self._ensure_connected()
        self.coords = {"x": float(x), "y": float(y), "z": float(z)}

    def move_to_well(self, row: int, column: int) -> None:
        self._ensure_connected()
        self.row = int(row)
        self.column = int(column)
        self.coords = {"x": 120.0 + row * 2.25, "y": 60.0 + column * 2.25, "z": 220.0}

    def set_pressure(self, pulse: float, refuel: float, runtime: int = 6000) -> None:
        self._ensure_connected()
        _ = runtime
        self.pressure = {"pulse": float(pulse), "refuel": float(refuel)}

    def print_droplets(
        self,
        count: int,
        frequency: int,
        pulse_width: int,
        refuel_width: int,
    ) -> None:
        self._ensure_connected()
        _ = (pulse_width, refuel_width)
        time.sleep(min(1.0, float(count) / max(1, frequency)))

    def emergency_stop(self) -> None:
        self.pressure = {"pulse": 0.0, "refuel": 0.0}

    def _ensure_connected(self) -> None:
        if not self.connected:
            raise RuntimeError("Robot adapter not connected")
