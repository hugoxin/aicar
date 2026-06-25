"""Vehicle model placeholders for simulation."""


class VehicleModel:
    """Simple placeholder for future sedan / SUV / MPV geometry."""

    def __init__(self, name: str, length_mm: int, width_mm: int, height_mm: int) -> None:
        self.name = name
        self.length_mm = length_mm
        self.width_mm = width_mm
        self.height_mm = height_mm

    def summary(self) -> str:
        return (
            f"{self.name}: "
            f"{self.length_mm} x {self.width_mm} x {self.height_mm} mm"
        )

