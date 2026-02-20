from __future__ import annotations

import glob
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from .base import RobotAdapter


@dataclass
class LegacyConfig:
    printing_platform_root: Path
    settings_path: Path
    dobot_port_override: str | None = None
    arduino_port_override: str | None = None


def _normalize_base(path: Path) -> str:
    return path.as_posix().rstrip("/") + "/"


class LegacyPlatformAdapter(RobotAdapter):
    """
    Non-invasive adapter around the existing printing-platform modules.
    It does not modify any source in printing-platform.
    """

    def __init__(self, config: LegacyConfig) -> None:
        self.config = config
        self.connected = False
        self.simulation = True
        self.coords = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.row = 0
        self.column = 0
        self.pressure = {"pulse": 0.0, "refuel": 0.0}
        self.platform = None
        self._robot_mod = None

    def connect(self, simulation: bool) -> None:
        self._prepare_import_paths()
        self._simulation = simulation
        self.simulation = simulation

        import Robot  # type: ignore
        import Arduino  # type: ignore
        import Regulator  # type: ignore

        self._robot_mod = Robot
        self._disable_interactive_fallbacks()

        with self.config.settings_path.open("r", encoding="utf-8") as fh:
            default_settings = json.load(fh)

        if self.config.dobot_port_override:
            default_settings["Dobot_port"] = self.config.dobot_port_override
        if self.config.arduino_port_override:
            default_settings["Arduino_port"] = self.config.arduino_port_override

        base_path = _normalize_base(self.config.printing_platform_root)
        default_settings["base_path"] = base_path

        class ServicePlatform(Robot.Robot, Arduino.Arduino, Regulator.Regulator):  # type: ignore
            def __init__(self, settings: dict, sim: bool) -> None:
                self.sim = sim
                self.default_settings = settings
                self.base = settings["base_path"]
                self.robot_type = settings["robot_type"]
                self.mode = settings["default_dispenser"]
                self.location = "unknown"
                self.current_row = 0
                self.current_column = 0
                self.keyboard_config = "api"
                self.pause = False
                self.terminate = False
                self.current_coords = {"x": 200.0, "y": 0.0, "z": 150.0}
                self.calibrated = False
                self.tracking_volume = False
                self._load_dispenser_defaults(self.mode)
                self.get_dobot_calibrations()

            def _load_dispenser_defaults(self, mode: str) -> None:
                cfg = self.default_settings["dispenser_types"][mode]
                self.height = cfg["height"]
                self.refuel_width = cfg["refuel_width"]
                self.pulse_width = cfg["pulse_width"]
                self.refuel_pressure = cfg["refuel_pressure"]
                self.pulse_pressure = cfg["pulse_pressure"]
                self.test_droplet_count_low = cfg["test_droplet_count_low"]
                self.test_droplet_count_high = cfg["test_droplet_count_high"]
                self.frequency = cfg["frequency"]
                self.max_volume = cfg["max_volume"]
                self.min_volume = cfg["min_volume"]
                self.current_volume = 0
                self.mode = mode

            def get_file_path(self, pattern: str, base: bool = False):
                p = f"{self.base}{pattern}" if base else pattern
                matches = sorted(glob.glob(p))
                if len(matches) == 1:
                    return matches[0]
                if len(matches) == 0:
                    raise FileNotFoundError(f"No match for pattern: {p}")
                raise RuntimeError(f"Ambiguous pattern (multiple matches): {p}")

            def get_all_paths(self, pattern: str, base: bool = False):
                p = f"{self.base}{pattern}" if base else pattern
                return sorted(glob.glob(p))

            def ask_yes_no(self, message: str = "") -> bool:
                _ = message
                raise RuntimeError("Interactive prompts are disabled in API mode")

            def ask_yes_no_quit(self, message: str = "") -> str:
                _ = message
                raise RuntimeError("Interactive prompts are disabled in API mode")

            def move_to_well(self, row: int, column: int) -> None:
                if row < 0 or column < 0 or row > self.max_rows or column > self.max_columns:
                    raise ValueError(f"Well out of range: row={row}, column={column}")
                target = self.get_well_coords(row, column)
                self.move_dobot(target["x"], target["y"], target["z"], verbose=False)
                self.current_row = int(row)
                self.current_column = int(column)

            def home_dobot_api(self) -> None:
                loading = self.calibration_data.get("loading")
                if not loading:
                    raise RuntimeError("Missing 'loading' position in print calibration")
                self.move_dobot(loading["x"], loading["y"], loading["z"], verbose=True)
                self.location = "loading"

            def print_droplets_api(
                self, count: int, frequency: int, pulse_width: int, refuel_width: int
            ) -> None:
                if count <= 0:
                    raise ValueError("count must be >= 1")
                if self.sim:
                    return
                self.ser.readall()
                self.print_command(frequency, pulse_width, refuel_width, count)
                time.sleep(count / max(1, frequency))
                retries = 0
                while True:
                    current = self.ser.read().decode(errors="ignore")
                    if current == "C":
                        break
                    time.sleep(0.05)
                    retries += 1
                    if retries > 20:
                        raise RuntimeError("Arduino did not acknowledge print completion")

        self.platform = ServicePlatform(default_settings, simulation)

        if not simulation:
            self.platform.init_pressure()
            self.platform.init_dobot(self.platform.default_settings["Dobot_port"])
            self.platform.init_ard(self.platform.default_settings["Arduino_port"])

        self.coords = dict(self.platform.current_coords)
        self.pressure = {
            "pulse": float(self.platform.pulse_pressure),
            "refuel": float(self.platform.refuel_pressure),
        }
        self.connected = True

    def disconnect(self) -> None:
        if not self.platform:
            self.connected = False
            return
        if not self.simulation:
            try:
                self.platform.close_ard()
            finally:
                try:
                    self.platform.pressure_off()
                finally:
                    try:
                        self.platform.close_reg()
                    finally:
                        self.platform.disconnect_dobot()
        self.connected = False

    def home(self) -> None:
        self._ensure_platform()
        self.platform.home_dobot_api()
        self.coords = dict(self.platform.current_coords)

    def move_xyz(self, x: float, y: float, z: float) -> None:
        self._ensure_platform()
        self.platform.move_dobot(x, y, z)
        self.coords = dict(self.platform.current_coords)

    def move_to_well(self, row: int, column: int) -> None:
        self._ensure_platform()
        self.platform.move_to_well(row, column)
        self.row = int(row)
        self.column = int(column)
        self.coords = dict(self.platform.current_coords)

    def set_pressure(self, pulse: float, refuel: float, runtime: int = 6000) -> None:
        self._ensure_platform()
        self.platform.set_pressure(pulse, refuel, runtime=runtime)
        self.pressure = {"pulse": float(pulse), "refuel": float(refuel)}

    def print_droplets(
        self,
        count: int,
        frequency: int,
        pulse_width: int,
        refuel_width: int,
    ) -> None:
        self._ensure_platform()
        self.platform.print_droplets_api(count, frequency, pulse_width, refuel_width)

    def emergency_stop(self) -> None:
        if self.platform and not self.simulation:
            try:
                self.platform.pressure_off()
            except Exception:
                pass
        self.pressure = {"pulse": 0.0, "refuel": 0.0}

    def _prepare_import_paths(self) -> None:
        scripts_path = self.config.printing_platform_root / "Scripts"
        root_path = self.config.printing_platform_root
        for p in [str(scripts_path), str(root_path)]:
            if p not in sys.path:
                sys.path.insert(0, p)

    def _disable_interactive_fallbacks(self) -> None:
        if self._robot_mod is None:
            return

        def _no_prompt(*args, **kwargs):
            _ = (args, kwargs)
            raise RuntimeError(
                "Interactive fallback was requested (likely missing default ports or calibration files). "
                "Fix settings/default paths instead."
            )

        self._robot_mod.select_options = _no_prompt

    def _ensure_platform(self) -> None:
        if self.platform is None or not self.connected:
            raise RuntimeError("Legacy platform adapter is not connected")
