from pydantic import BaseModel, Field


class ConnectRequest(BaseModel):
    simulation: bool = Field(default=True, description="Run in simulation mode")


class MoveXYZRequest(BaseModel):
    x: float
    y: float
    z: float


class MoveToWellRequest(BaseModel):
    row: int = Field(ge=0)
    column: int = Field(ge=0)


class SetPressureRequest(BaseModel):
    pulse: float
    refuel: float
    runtime: int = Field(default=6000, ge=1)


class PrintDropletsRequest(BaseModel):
    count: int = Field(ge=1)
    frequency: int = Field(default=20, ge=1)
    pulse_width: int = Field(default=3000, ge=0)
    refuel_width: int = Field(default=47000, ge=0)


class RobotStatus(BaseModel):
    connected: bool
    simulation: bool
    mode: str
    busy: bool
    current_row: int
    current_column: int
    coords: dict
    pressure: dict
    last_error: str | None = None
