from pathlib import Path
import pydantic


class UVARS(pydantic.BaseModel):
    copy_anat: pydantic.FilePath
    final_anat: pydantic.FilePath
    template: pydantic.FilePath
    ss_review_dset: pydantic.FilePath
    subj: str
    ses: str | None = None
    mask_dset: pydantic.FilePath | None = None
    vr_base_dset: pydantic.FilePath | None = None

    @property
    def figures_dir(self) -> Path:
        top = Path(self.subj) / self.ses if self.ses else Path(self.subj)
        return top / "figures"
