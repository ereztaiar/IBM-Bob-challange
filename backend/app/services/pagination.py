"""Reusable pagination helper.

Provides a single :class:`PaginationParams` dataclass consumed by service
functions to build ``LIMIT``/``OFFSET`` queries.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class PaginationParams:
    """Immutable pagination parameters.

    Attributes:
        page: 1-based page number.
        page_size: Number of items per page (clamped to :data:`MAX_PAGE_SIZE`).
    """

    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    @property
    def offset(self) -> int:
        """Compute the SQL ``OFFSET`` value.

        Returns:
            Zero-based row offset for the requested page.
        """
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return the effective ``LIMIT`` value (clamped).

        Returns:
            Page size clamped to :data:`MAX_PAGE_SIZE`.
        """
        return min(self.page_size, MAX_PAGE_SIZE)
