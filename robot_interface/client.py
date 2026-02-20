from __future__ import annotations

import requests


class DobbieRobotClient:
    def __init__(self, base_url: str, timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> dict:
        return self._get("/health")

    def status(self) -> dict:
        return self._get("/status")

    def connect(self, simulation: bool = True) -> dict:
        return self._post("/connect", {"simulation": simulation})

    def disconnect(self) -> dict:
        return self._post("/disconnect", {})

    def home(self) -> dict:
        return self._post("/robot/home", {})

    def move_xyz(self, x: float, y: float, z: float) -> dict:
        return self._post("/robot/move_xyz", {"x": x, "y": y, "z": z})

    def move_to_well(self, row: int, column: int) -> dict:
        return self._post("/robot/move_to_well", {"row": row, "column": column})

    def set_pressure(self, pulse: float, refuel: float, runtime: int = 6000) -> dict:
        return self._post(
            "/pressure/set",
            {"pulse": pulse, "refuel": refuel, "runtime": runtime},
        )

    def print_droplets(
        self,
        count: int,
        frequency: int = 20,
        pulse_width: int = 3000,
        refuel_width: int = 47000,
    ) -> dict:
        return self._post(
            "/print/droplets",
            {
                "count": count,
                "frequency": frequency,
                "pulse_width": pulse_width,
                "refuel_width": refuel_width,
            },
        )

    def emergency_stop(self) -> dict:
        return self._post("/emergency_stop", {})

    def _get(self, path: str) -> dict:
        r = requests.get(f"{self.base_url}{path}", timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, payload: dict) -> dict:
        r = requests.post(f"{self.base_url}{path}", json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()
