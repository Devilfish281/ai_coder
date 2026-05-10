# src/test_browser_mcp/tools/my_utils/database_version_info.py

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DatabaseVersionInfo:
    """Central version structure for DB compatibility and future migrations."""

    major: int
    minor: int
    patch: int
    description: str

    @property
    def semver(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @property
    def display_version(self) -> str:
        return f"{self.description} ({self.semver})"
