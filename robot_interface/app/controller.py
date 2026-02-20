from __future__ import annotations

from threading import Lock

from .adapters.base import RobotAdapter
from .models import RobotStatus


class RobotController:
    def __init__(self, adapter: RobotAdapter) -> None:
        self.adapter = adapter
        self._lock = Lock()
        self.connected = False
        self.simulation = True
        self.mode = "droplet"
        self.busy = False
        self.current_row = 0
        self.current_column = 0
        self.coords = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.pressure = {"pulse": 0.0, "refuel": 0.0}
        self.last_error: str | None = None

    def connect(self, simulation: bool) -> None:
        with self._lock:
            self._set_busy(True)
            try:
                self.adapter.connect(simulation=simulation)
                self.connected = True
                self.simulation = simulation
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise
            finally:
                self._set_busy(False)

    def disconnect(self) -> None:
        with self._lock:
            self._set_busy(True)
            try:
                self.adapter.disconnect()
                self.connected = False
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise
            finally:
                self._set_busy(False)

    def home(self) -> None:
        with self._lock:
            self._require_connected()
            self._set_busy(True)
            try:
                self.adapter.home()
                self.coords = getattr(self.adapter, "coords", self.coords)
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise
            finally:
                self._set_busy(False)

    def move_xyz(self, x: float, y: float, z: float) -> None:
        with self._lock:
            self._require_connected()
            self._set_busy(True)
            try:
                self.adapter.move_xyz(x, y, z)
                self.coords = {"x": x, "y": y, "z": z}
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise
            finally:
                self._set_busy(False)

    def move_to_well(self, row: int, column: int) -> None:
        with self._lock:
            self._require_connected()
            self._set_busy(True)
            try:
                self.adapter.move_to_well(row, column)
                self.current_row = row
                self.current_column = column
                self.coords = getattr(self.adapter, "coords", self.coords)
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise
            finally:
                self._set_busy(False)

    def set_pressure(self, pulse: float, refuel: float, runtime: int = 6000) -> None:
        with self._lock:
            self._require_connected()
            self._set_busy(True)
            try:
                self.adapter.set_pressure(pulse, refuel, runtime=runtime)
                self.pressure = {"pulse": pulse, "refuel": refuel}
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise
            finally:
                self._set_busy(False)

    def print_droplets(
        self, count: int, frequency: int, pulse_width: int, refuel_width: int
    ) -> None:
        with self._lock:
            self._require_connected()
            self._set_busy(True)
            try:
                self.adapter.print_droplets(count, frequency, pulse_width, refuel_width)
                self.last_error = None
            except Exception as exc:
                self.last_error = str(exc)
                raise
            finally:
                self._set_busy(False)

    def emergency_stop(self) -> None:
        with self._lock:
            try:
                self.adapter.emergency_stop()
                self.pressure = {"pulse": 0.0, "refuel": 0.0}
            finally:
                self._set_busy(False)

    def status(self) -> RobotStatus:
        return RobotStatus(
            connected=self.connected,
            simulation=self.simulation,
            mode=self.mode,
            busy=self.busy,
            current_row=self.current_row,
            current_column=self.current_column,
            coords=self.coords,
            pressure=self.pressure,
            last_error=self.last_error,
        )

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy

    def _require_connected(self) -> None:
        if not self.connected:
            raise RuntimeError("Robot is not connected")
