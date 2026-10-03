"""Core Cleaner engine for removing validated temporary and cache files."""

import os
from pathlib import Path
import stat
from typing import Callable, List, Optional, Set

from app.cleaner.safety import SafetyValidator
from app.models.file_item import CleanResult, FileItem
from app.utils.logging import get_logger


class SystemCleaner:
    """Safely executes deletion of validated files."""

    def __init__(self, safety_validator: SafetyValidator):
        self.validator = safety_validator
        self.logger = get_logger()

    def clean_items(
        self,
        items: List[FileItem],
        progress_callback: Optional[Callable[[int, int, int, str], None]] = None,
        cancel_requested: Optional[Callable[[], bool]] = None,
    ) -> List[CleanResult]:
        """
        Deletes selected items with safety verification and progress reporting.
        progress_callback signature: (current_idx, total_count, freed_bytes, current_path_name)
        """
        results: List[CleanResult] = []
        selected_items = [item for item in items if item.is_selected]
        total = len(selected_items)
        freed_bytes = 0

        self.logger.info(f"Starting cleanup process for {total} selected items.")

        # Build scan paths set for validation
        scan_paths: Set[Path] = set()
        for item in items:
            try:
                scan_paths.add(Path(os.path.realpath(str(item.path))).resolve())
            except Exception:
                scan_paths.add(item.path)

        for idx, item in enumerate(selected_items, start=1):
            if cancel_requested and cancel_requested():
                self.logger.info("Cleanup cancelled by user request.")
                break

            path = item.path

            # Validate safety
            is_safe, reason = self.validator.validate_delete(path, scan_set_paths=scan_paths)

            if not is_safe:
                self.logger.warning(f"Skipped deletion for '{path.name}': {reason}")
                results.append(
                    CleanResult(
                        path=path,
                        category=item.category,
                        success=False,
                        freed_bytes=0,
                        error_reason=reason,
                    )
                )
            else:
                # Attempt deletion
                try:
                    # Clear read-only attribute if present
                    try:
                        os.chmod(path, stat.S_IWRITE)
                    except Exception:
                        pass

                    if path.is_file():
                        file_size = item.size
                        path.unlink()
                        freed_bytes += file_size
                        results.append(
                            CleanResult(
                                path=path,
                                category=item.category,
                                success=True,
                                freed_bytes=file_size,
                            )
                        )
                    elif path.is_dir():
                        # Delete directory contents or folder
                        try:
                            # Only delete if empty or safe
                            path.rmdir()
                            results.append(
                                CleanResult(
                                    path=path,
                                    category=item.category,
                                    success=True,
                                    freed_bytes=item.size,
                                )
                            )
                        except OSError as e:
                            results.append(
                                CleanResult(
                                    path=path,
                                    category=item.category,
                                    success=False,
                                    freed_bytes=0,
                                    error_reason=f"Could not remove folder: {e}",
                                )
                            )

                except PermissionError:
                    results.append(
                        CleanResult(
                            path=path,
                            category=item.category,
                            success=False,
                            freed_bytes=0,
                            error_reason="File currently in use / Permission denied",
                        )
                    )
                except FileNotFoundError:
                    results.append(
                        CleanResult(
                            path=path,
                            category=item.category,
                            success=True,
                            freed_bytes=0,
                            error_reason="File already removed",
                        )
                    )
                except Exception as err:
                    results.append(
                        CleanResult(
                            path=path,
                            category=item.category,
                            success=False,
                            freed_bytes=0,
                            error_reason=str(err),
                        )
                    )

            if progress_callback:
                progress_callback(idx, total, freed_bytes, path.name)

        successful = sum(1 for r in results if r.success)
        failed = total - successful
        self.logger.info(
            f"Cleanup finished. Freed: {freed_bytes} bytes. Success: {successful}, Failed: {failed}."
        )
        return results
