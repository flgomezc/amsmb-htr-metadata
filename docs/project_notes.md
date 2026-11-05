# Project notes

Notes for anyone working in this repository, with or without an AI assistant. For the project's goals, see the root `README.md`.

## Commit messages

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/).

## Repository layout

The layout is modeled on Cookiecutter Data Science:

- `data/sample/`: a sample of the published dataset that keeps its structure. This project works on the metadata, not the data, so treat it as read-only.
- `metadata/`: the metadata this project produces, in `croissant/`, `ddi-cdi/`, and `w3c_annotations/`.
- `environments/`: environment definitions.
- `src/`: reusable code.
- `notebooks/`: exploratory work.
- `docs/`: project documentation.

There is no code yet, so there is no build, lint, or test tooling. Directories with no content yet hold a `.gitkeep`; remove it once the directory has real files.

## Source data: `data/sample/`

This is a 2-document subset of the 100-document AMSMB HTR dataset: medieval notarial charters on parchment, 1208-1499, mainly in Medieval Latin with some Medieval Catalan. The original is on [BSC Dataverse](https://dataverse.bsc.es/dataset.xhtml?persistentId=perma:BSC/0VB0MC) under CC BY-SA 4.0. `Datasheet.pdf` documents the full dataset, including transcription conventions and vocabularies.

Each document is identified by its `reference`, which links these files:

| File | Coverage | Contents |
| --- | --- | --- |
| `data/{train,test}/<reference>.jpg` | Subset only (2 documents) | Page image |
| `data/{train,test}/<reference>.xml` | Subset only (2 documents) | PageXML (2019-07-15 schema) exported from eScriptorium; `Page/@imageFilename` names the image in the same directory |
| `metadata.csv` | Full dataset (100 rows) | `reference, split, date, archive, signature, scrivener/notary, type, material, folder` |
| `amsmb_metadata_with_summaries.json` | Subset only (2 records) | The CSV fields plus a Catalan `summary`. Prepared for publication on Dataverse; not part of V1 |

The subset contains `AMSMB_1-1-17` (train) and `AMSMB_1-3-100` (test). There is no `data/validation/` directory, although `metadata.csv` has 20 validation rows.

## Local Data pitfalls

- **Most CSV rows have no local files.** 98 of the 100 rows refer to documents that aren't in this repository, so filter to the subset before joining against `data/`.
- **The hand field has two names.** It is `scrivener/notary` in the CSV and `hand` in the JSON.
- **Don't derive `reference` from `signature`.** `AMSMB_1-1-17` has signature `1-1-7` in both the CSV and JSON, while the datasheet and filename use `1-1-17`. It is the only such mismatch in the CSV, so it looks like an error in the source. Use `reference` as the key, and don't silently correct the value.
- **`date` is a year only.** It is an integer in the JSON and a string when read from the CSV.
- **`type` and `summary` are in modern Catalan.** The transcriptions are Latin and Ancient Catalan.

## PageXML structure

- **Layout types:** types use a simplified SegmOnto vocabulary and are stored in the `custom` attribute, for example `structure {type:MainZone;}`, not in the PAGE `type` attribute, so they must be parsed out of that string.
  - Regions: `MainZone`, `MarginTextZone`, `DropCapitalZone`, `GraphicZone:Signum`, `GraphicZone:Other`
  - Lines: `DefaultLine`, `InterlinearLine`
- **Missing types:** `custom` can be absent. 13 of the 24 lines and one region in `AMSMB_1-3-100.xml` have none, so don't assume every element is typed.
- **Regions without text:** in these two files, only `MainZone` regions contain `TextLine`s, and a page can have several of them. Signum and drop capital regions have only `Coords`.
- **Line geometry:** each `TextLine` has `Coords` (polygon), `Baseline`, and `TextEquiv/Unicode`. IDs look like `eSc_line_*` and `eSc_textblock_*`.
- **Coordinates:** these are pixels in the JPG, and `Page` gives `imageWidth` and `imageHeight`.

## Transcription conventions

Transcription conventions are explained in `data/sample/Datasheet.pdf`.

Transcriptions are semi-diplomatic, which matters when treating the text as data:

- Abbreviations are expanded, except abbreviated first names such as `B.`.
- Punctuation and capitalization are normalized, but spelling irregularities are kept.
- Proper names are not modernized or translated, so `Fontisrubei` stays as written.
- A line is not always a complete written line: a large gap or a cross signature splits it into separate `TextLine`s, as in `Sig` / `num Petri de Bages...`. `+` marks a cross signature within a line, as in `Sig+num`.

## Environment

`environments/amsmb-htr-metadata.yml` defines the project's conda environment. It uses `conda-forge` with `nodefaults`, not Anaconda's official channels.

```bash
conda env create -f environments/amsmb-htr-metadata.yml
```

The environment provides `pdftotext` and `pdftoppm` for reading PDFs such as `data/sample/Datasheet.pdf`.
