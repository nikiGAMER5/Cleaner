"""ScanResultSet and CategorySummary data models."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.models.file_item import FileItem


@dataclass
class CategorySummary:
    """Summary metrics for a specific scan category."""
    category: str
    file_count: int
    total_size: int
    selected_count: int
    selected_size: int


@dataclass
class ScanResultSet:
    """Aggregates all results from a full system scan."""
    items: List[FileItem] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    recycle_bin_size: int = 0
    recycle_bin_count: int = 0

    @property
    def duration(self) -> float:
        return max(0.0, self.end_time - self.start_time)

    @property
    def total_size(self) -> int:
        return sum(item.size for item in self.items)

    @property
    def total_count(self) -> int:
        return len(self.items)

    @property
    def selected_size(self) -> int:
        return sum(item.size for item in self.items if item.is_selected)

    @property
    def selected_count(self) -> int:
        return sum(1 for item in self.items if item.is_selected)

    def get_items_by_category(self, category: str) -> List[FileItem]:
        return [item for item in self.items if item.category == category]

    def get_category_summary(self, category: str) -> CategorySummary:
        items = self.get_items_by_category(category)
        return CategorySummary(
            category=category,
            file_count=len(items),
            total_size=sum(i.size for i in items),
            selected_count=sum(1 for i in items if i.is_selected),
            selected_size=sum(i.size for i in items if i.is_selected),
        )

    def get_summaries(self) -> Dict[str, CategorySummary]:
        categories = {item.category for item in self.items}
        return {cat: self.get_category_summary(cat) for cat in categories}
