from functools import partial
from typing import overload

import bids2table as b2t
import polars as pl
import pyarrow as pa
from bids2table._pathlib import PathT, as_path
from templateflow import api as tflow


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


def _query_dataset(table: pl.DataFrame, query: str) -> pl.DataFrame:
    """Query for a specific thing via SQL queries."""
    return table.sql(f"SELECT * FROM self WHERE {query}")


def _get_fpath(table: pl.DataFrame) -> str:
    """Grab absolute file path of file."""
    return str(as_path("/".join(table.select(["root", "path"]).row(0))).resolve())


def create_afni_json(unique_table: pl.DataFrame, out_dir: PathT) -> dict[str, str]:
    """Query a unique table (e.g. sub, ses, run, etc.) for specific files."""

    def _create_ss_review_dset(repetitions: int, out_dir: PathT) -> str:
        """Create out.ss_review.FT.txt with the number of TRs per run as needed."""
        out_fpath = (out_dir / "out.ss_review.FT.txt").resolve()
        out_fpath.write_text(f"num_TRs_per_run: {repetitions}")
        return str(out_fpath)

    subject_query = partial(_query_dataset, unique_table)
    subject = unique_table.select("sub")[0].item()

    # Create base JSON file
    # NOTE_1: Need to rethink querying to be more flexible (e.g. space, run, etc.)
    # NOTE_2: Is there another way to grab the templateflow templates (s3?)
    afni_json = {
        "copy_anat": _get_fpath(
            table=subject_query(
                query="datatype = 'anat' AND space = 'MNI152NLin2009cAsym' AND desc = 'preproc' AND suffix = 'T1w' AND ext = '.nii.gz'"
            )
        ),
        "final_anat": _get_fpath(
            table=subject_query(
                query="datatype = 'anat' AND space = 'MNI152NLin2009cAsym' AND desc = 'preproc' AND suffix = 'T1w' AND ext = '.nii.gz'"
            )
        ),
        "template": str(
            tflow.get(
                template="MNI152NLin2009cAsym",
                desc=None,
                resolution=2,
                suffix="T1w",
                extension=".nii.gz",
            )
        ),
        "ss_review_dset": _create_ss_review_dset(repetitions=1, out_dir=out_dir),
        "subj": f"sub-{subject}" if not subject.startswith("sub") else {subject},
        "mask_dset": _get_fpath(
            table=subject_query(
                query="datatype = 'func' AND task = 'balloonanalogrisktask' AND desc = 'brain' AND suffix = 'mask' AND ext = '.nii.gz'"
            )
        ),
        "vr_base_dset": _get_fpath(
            table=subject_query(
                query="datatype = 'func' AND task = 'balloonanalogrisktask' AND suffix = 'boldref' AND ext = '.nii.gz'"
            )
        ),
    }

    return afni_json


if __name__ == "__main__":
