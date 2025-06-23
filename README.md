# bids2afniqcjson

## Example Usage

Here, we will experiment with `ds000001`, which has [fmriprep derivatives hosted on OpenNeuro](https://openneuro.org/datasets/ds000001/versions/1.0.0/derivatives). Pull only the functional and anatomical data associated with sub-01.

```shell
aws s3 \
  sync --no-sign-request \
  --exclude "sub*" \
  --exclude "sourcedata/freesurfer/*" \
  --include "sourcedata/freesurver/sub-01/*" \
  --exclude "sourcedata/raw/*" \
  --include "sub-01/func/*" \
  s3://openneuro-derivatives/fmriprep/ds000001-fmriprep sourcedata/ds000001-fmriprep
```

```shell
$ bids2afniqcjson sourcedata/ds000001-fmriprep derivatives/afnifigures
2025-06-23 14:12:01,188 | INFO     | ++ Done making (executable) IC pbrun script: 
2025-06-23 14:12:01,189 | INFO     |       run_instacorr_pbrun.tcsh
2025-06-23 14:12:01,189 | INFO     | ++ Done making (executable) GV pbrun script: 
2025-06-23 14:12:01,189 | INFO     |       run_graphview_pbrun.tcsh
2025-06-23 14:12:01,189 | INFO     | ++ APQC create: qc_00_vorig_EPI
2025-06-23 14:12:07,281 | INFO     | ++ APQC create: qc_01_vorig_anat
2025-06-23 14:12:12,969 | INFO     | ++ APQC create: qc_02_vorig_olap
2025-06-23 14:12:19,260 | INFO     | ++ APQC create: qc_03_va2t_anat2temp
2025-06-23 14:12:27,704 | INFO     | ++ APQC create: qc_04_va2t_mask2final
2025-06-23 14:12:33,398 | INFO     | ++ APQC create: qc_05_qsumm_ssrev
2025-06-23 14:12:33,408 | INFO     | ++ APQC create: copy jsons to info dir
2025-06-23 14:12:33,418 | INFO     | ++ APQC create: copy ss_review_basic file
2025-06-23 14:12:33,458 | INFO     | ++ APQC create: display ss_review_basic info
2025-06-23 14:12:33,467 | INFO     | num_TRs_per_run: 1
2025-06-23 14:12:33,467 | INFO     | # ++++++++++++++ Check output of @ss_review_basic ++++++++++++++ #
2025-06-23 14:12:33,467 | INFO     | ------------------------------------------------------------------
2025-06-23 14:12:33,467 | INFO     | ------------------------------------------------------------------
2025-06-23 14:12:33,467 | INFO     | 
2025-06-23 14:12:33,467 | INFO     | ++ Done setting up QC dir: QC_sub-01
2025-06-23 14:12:33,467 | INFO     |    To create the APQC HTML, run either this (from any location):      
2025-06-23 14:12:33,467 | INFO     |      
2025-06-23 14:12:33,467 | INFO     |        apqc_make_html.py -qc_dir /private/var/folders/v_/kcpb096s1m3_37ctfd2sp2xm0000gn/T/tmpjn3lj43s/QC_sub-01
2025-06-23 14:12:33,467 | INFO     | 
2025-06-23 14:12:33,467 | INFO     |    ... or this (from the afni_proc.py results directory):
2025-06-23 14:12:33,467 | INFO     | 
2025-06-23 14:12:33,467 | INFO     |        apqc_make_html.py -qc_dir QC_sub-01
2025-06-23 14:12:33,467 | INFO     | 
2025-06-23 14:12:33,467 | INFO     | 
2025-06-23 14:12:33,486 | INFO     | Executed apqc_make_tcsh.py in 0:00:32.932509
```

## AFNI Fields Implemented

The following list indicates which AFNI Proc UVARS fields will be filled by `bids2afniqcjson`.

As development continues, more fields will be extracted.

- [x] afni_package
- [x] afni_ver
- [ ] align_anat
- [ ] censor_dset
- [x] copy_anat
- [ ] cormat_warn_dset
- [ ] df_info_dset
- [ ] enorm_dset
- [ ] errts_dset
- [x] final_anat
- [ ] final_epi_dset
- [ ] final_view
- [ ] flip_check_dset
- [ ] flip_guess
- [ ] gcor_dset
- [ ] have_radcor_dirs
- [ ] mask_anat_templ_corr_dset
- [ ] mask_corr_dset
- [x] mask_dset
- [ ] max_4095_warn_dset
- [ ] mb_level
- [ ] mot_limit
- [ ] motion_dset
- [ ] name
- [ ] nt_applied
- [ ] nt_orig
- [ ] num_stim
- [ ] out_limit
- [ ] outlier_dset
- [ ] pre_ss_warn_dset
- [ ] rm_trs
- [ ] slice_pattern
- [x] ss_review_dset
- [ ] stats_dset
- [ ] subj
- [ ] sum_ideal
- [ ] tcat_dset
- [x] template
- [ ] tr
- [ ] tsnr_dset
- [ ] vlines_tcat_dir
- [ ] volreg_dset
- [x] vr_base_dset
- [ ] xmat_regress
