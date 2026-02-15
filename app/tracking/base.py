from __future__ import annotations

from abc import ABC, abstractmethod

from app.types import HeadPose


class Tracker(ABC):
    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_latest_pose(self) -> HeadPose:
        raise NotImplementedError
