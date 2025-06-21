from typing import overload

import bids2table as b2t
import polars as pl
import pyarrow as pa
from bids2table._pathlib import PathT, as_path


@overload
def _format_subjects(subjects: str) -> str: ...


@overload
def _format_subjects(subjects: list[str]) -> list[str]: ...


def _format_subjects(subjects: str | list[str]) -> str | list[str]:
    """Format subject string (i.e. add 'sub-' if not provided)."""

    def _format_subject(subject: str) -> str:
        return f"sub-{subject}" if not subject.startswith("sub-") else subject

    if isinstance(subjects, list):
        return [_format_subject(subject) for subject in subjects]
    else:
        return _format_subject(subjects)


def load_dataset(
    ds_path: str | PathT, subjects: str | list[str] | None = None
) -> pl.DataFrame:
    """Ingest local / cloud BIDS dataset, returning Polars dataframe of files."""
    if subjects is not None:
        subjects = _format_subjects(subjects)

    table = b2t.index_dataset(as_path(ds_path), include_subjects=subjects)
    # Flatten extra entities and drop column
    extra_entities = table["extra_entities"].to_pylist()
    extra_entities_dicts = [
        dict(pairs) if isinstance(pairs, list) else {} for pairs in extra_entities
    ]
    all_keys = set().union(*(d.keys() for d in extra_entities_dicts))

    # No extra entities
    if not all_keys:
        return pl.from_arrow(table.drop(["extra_entities"]))

    # Flatten and merge extra entities
    extra_entities_dicts = [
        {k: d.get(k) for k in all_keys} for d in extra_entities_dicts
    ]
    extra_table = pa.Table.from_pylist(extra_entities_dicts)
    extra_table = extra_table.append_column("path", table["path"])
    table = table.drop(["extra_entities"]).join(extra_table, keys=["path"])

    return pl.from_arrow(table)


if __name__ == "__main__":
    ...
