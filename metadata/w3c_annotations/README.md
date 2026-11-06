# W3C Web Annotations

## Goal

Describe the AMSMB charters with W3C Web Annotations: zones, text lines with their transcription, and baselines. The meaning of each shape comes from external vocabularies: the PAGE schema and SegmOnto.

## Why W3C

- DDI-CDI 1.0 has no native support for annotations. It can attach an annotation file by URI, but
  it cannot see inside it.
- [Issue #29](https://github.com/ddi-cdi/ddi-cdi/issues/29) in the DDI-CDI repository proposes W3C
  annotations as the default, with links to annotations in other vocabularies such as PageXML.
  These experiments are a test case for it.
- The annotations describe the files and point to them. They are not a copy of the dataset: the
  images and the PageXML stay in the repository. A full copy would be the 1:1 map in Borges' "Del
  rigor en la ciencia".

## Current design

From `20261106_textline_baseline/`. Each line has two annotations: one for the text area and its
transcription, and one for the baseline.

```
AnnotationPage
└─ items
   ├─ zone       motivation: classifying
   │   ├─ body:   PAGE TextRegion (classifying) · SegmOnto type (tagging) · TextRegion in the PageXML (identifying)
   │   └─ target: image + polygon (SvgSelector)
   ├─ line       motivation: describing
   │   ├─ body:   transcription · PAGE TextLine (classifying) · SegmOnto type (tagging)
   │   │          · TextLine in the PageXML (identifying) · its zone annotation (linking)
   │   └─ target: image + polygon (SvgSelector)
   └─ baseline   motivation: classifying
       ├─ body:   PAGE Baseline (classifying) · Baseline in the PageXML (identifying) · its line annotation (linking)
       └─ target: image + polyline (SvgSelector)
```

All motivations and purposes come from the W3C vocabulary. The PAGE schema and SegmOnto only give
the values: what each shape is.

## Experiments

Each folder is one experiment, named by the date it started.

| Folder | What it tests |
| --- | --- |
| `20261007_pagexml_viewer/` | The first converter (`pagexml2w3c.py` and two viewers). Baselines are not converted; each annotation links to its element in the PageXML. |
| `20261008_noemi_experiment/` | Noemi's draft: the baseline as its own annotation, a polyline, with the PAGE schema as its body. |
| `20261017_html_viewer/` | Compares both ways of handling baselines on one charter: only linked to the PageXML, or also stored as polylines. |
| `20261106_textline_baseline/` | The current design: both approaches together, with every baseline explicit. |

## Open points

- Noemi's feedback on the current design, for example `classifying` or `identifying` for the baseline.
