import argparse
import logging
import tempfile
from functools import partial
from pathlib import Path
from typing import overload

import bids2table as b2t
import polars as pl
import pyarrow as pa
from bids2table._pathlib import PathT, as_path
from niwrap_afni import afni
from templateflow import api as tflow

from bids2afniqcjson import models

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s", level=logging.INFO
)


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


def create_afni_json(table: pl.DataFrame, subject: str, out_dir: PathT) -> models.UVARS:
    """Query a unique table (e.g. sub, ses, run, etc.) for specific files."""

    def _create_ss_review_dset(repetitions: int, out_dir: PathT) -> str:
        """Create out.ss_review.FT.txt with the number of TRs per run as needed."""
        out_fpath = (out_dir / "out.ss_review.FT.txt").resolve()
        out_fpath.write_text(f"num_TRs_per_run: {repetitions}")
        return str(out_fpath)

    subject_table = table.filter(pl.col("sub") == subject)
    subject_query = partial(_query_dataset, subject_table)

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
        "subj": (f"sub-{subject}" if not subject.startswith("sub") else {subject}),
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

    return models.UVARS(**afni_json)


def create_figures(table: pl.DataFrame, dst: Path):
    if not dst.exists():
        dst.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmpd:
        with tempfile.NamedTemporaryFile(suffix=".json", dir=tmpd) as uvars_f:
            uvars_path = Path(uvars_f.name)
            for subject in table["sub"].unique().sort().to_list():
                uvars = create_afni_json(table=table, subject=subject, out_dir=dst)
                uvars_path.write_text(uvars.model_dump_json(exclude_none=True))
                with tempfile.TemporaryDirectory() as sub_dir:
                    afni.apqc_make_tcsh_py(
                        uvar_json=str(uvars_path),
                        review_style="pythonic",
                        subj_dir=sub_dir,
                    )
                    figures_dir = dst / uvars.figures_dir
                    if not figures_dir.exists():
                        figures_dir.mkdir(parents=True)
                    for jpg in Path(sub_dir).rglob("*jpg"):
                        jpg.rename(figures_dir / jpg.name)


def _main(
    bids_dir: PathT, out_dir: Path, include: str | list[str] | None = None
) -> None:
    table = load_dataset(ds_path=bids_dir, subjects=include)
    create_figures(table, dst=out_dir)


def main() -> None:
    # Command-line
    parser = argparse.ArgumentParser(
        prog="bids2afniqcjson",
        usage="bids2afniqc bids_dir [options]",
        description="Convert bids dataset for json for AFNI qc",
    )
    parser.add_argument(
        "bids_dir", action="store", type=Path, help="Path to BIDS dataset."
    )
    parser.add_argument(
        "out_dir", action="store", type=Path, help="Path to BIDS dataset."
    )
    parser.add_argument(
        "--include",
        default=None,
        type=str,
        nargs="*",
        help="Space separated list of subject(s) to process",
    )

    args = parser.parse_args()
    _main(args.bids_dir, out_dir=args.out_dir, include=args.include)


if __name__ == "__main__":
    main()
