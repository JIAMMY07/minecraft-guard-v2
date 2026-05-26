from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class WindowGeometry:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)

    @property
    def is_readable_size(self) -> bool:
        return self.width >= 320 and self.height >= 240

    def as_dict(self) -> dict[str, int | bool]:
        data = asdict(self)
        data.update({"width": self.width, "height": self.height, "is_readable_size": self.is_readable_size})
        return data

