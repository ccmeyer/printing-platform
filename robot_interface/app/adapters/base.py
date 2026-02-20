from __future__ import annotations

from abc import ABC, abstractmethod


class RobotAdapter(ABC):
    @abstractmethod
    def connect(self, simulation: bool) -> None:
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def home(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def move_xyz(self, x: float, y: float, z: float) -> None:
        raise NotImplementedError

    @abstractmethod
    def move_to_well(self, row: int, column: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def set_pressure(self, pulse: float, refuel: float, runtime: int = 6000) -> None:
        raise NotImplementedError

    @abstractmethod
    def print_droplets(
        self,
        count: int,
        frequency: int,
        pulse_width: int,
        refuel_width: int,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def emergency_stop(self) -> None:
        raise NotImplementedError
