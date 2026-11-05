#!/usr/bin/env python3
"""Convert eScriptorium PageXML files into W3C Web Annotation pages (JSON-LD).

One output file per charter: an AnnotationPage holding
  - one annotation per TextRegion (its SegmOnto zone type as a tag), and
  - one annotation per TextLine (the transcription, plus its SegmOnto line type as a tag).
Each annotation targets the charter's JPEG with an SvgSelector (the polygon)
and a FragmentSelector (its bounding box). The W3C model has no baseline
concept, so each annotation also carries a "linking" body that points to its
TextLine or TextRegion inside the PageXML file (XPathSelector). The baseline
and all other PageXML metadata stay one step away, and the PageXML remains
the master copy.

Motivations use only the W3C vocabulary: "describing" for transcriptions,
"classifying" for zone types. (IIIF viewers would prefer "supplementing".)

Usage:
  python3 pagexml2w3c.py OUT_DIR file1.xml [file2.xml ...] [--instances amsmb_charters_instances.jsonld]

With --instances, the image IRI is the charter's Dataverse JPEG link
(amsmb:hasPhysicalInstance) and the PageXML IRI is its Dataverse XML link
(amsmb:hasLogicalAnnotation), matched by file stem. Without it, the image
filename from the PageXML and the XML file name are used.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "https://dataverse.bsc.es/dataset.xhtml?persistentId=perma:BSC/0VB0MC#"
TRANSCRIBER = "https://orcid.org/0000-0003-2099-3567"  # Ramon Sarobe (Step07 in the model)
GENERATOR = NS + "tool_eScriptorium"


def local(tag):
    return tag.rsplit("}", 1)[-1]


def children(el, name):
    return [c for c in el if local(c.tag) == name]


def first(el, name):
    c = children(el, name)
    return c[0] if c else None


def points(el):
    coords = first(el, "Coords")
    if coords is None or not coords.get("points"):
        return []
    return [tuple(int(float(v)) for v in p.split(",")) for p in coords.get("points").split()]


def segmonto_type(el):
    m = re.search(r"structure\s*\{[^}]*type:([^;}]+)", el.get("custom", ""))
    return m.group(1).strip() if m else None


def selectors(pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    poly = " ".join(f"{x},{y}" for x, y in pts)
    return [
        {"type": "SvgSelector", "value": f'<svg><polygon points="{poly}" /></svg>'},
        {
            "type": "FragmentSelector",
            "conformsTo": "http://www.w3.org/TR/media-frags/",
            "value": f"xywh=pixel:{min(xs)},{min(ys)},{max(xs) - min(xs)},{max(ys) - min(ys)}",
        },
    ]


def tag_body(value):
    return {"type": "TextualBody", "purpose": "tagging", "value": value}


def xml_link(xml_iri, element, el_id):
    # local-name() because PageXML declares a default namespace
    return {
        "type": "SpecificResource",
        "purpose": "linking",
        "source": {"id": xml_iri, "format": "application/xml"},
        "selector": {"type": "XPathSelector", "value": f"//*[local-name()='{element}'][@id='{el_id}']"},
    }


def convert(xml_path, image_iri=None, xml_iri=None):
    root = ET.parse(xml_path).getroot()
    page = next(e for e in root.iter() if local(e.tag) == "Page")
    stem = Path(xml_path).stem
    source = {
        "id": image_iri or page.get("imageFilename"),
        "type": "Image",
        "format": "image/jpeg",
        "width": int(page.get("imageWidth")),
        "height": int(page.get("imageHeight")),
    }
    xml_iri = xml_iri or Path(xml_path).name
    base = f"{NS}anno_{stem}_"
    items = []
    for region in (e for e in page.iter() if local(e.tag) == "TextRegion"):
        rpts = points(region)
        if len(rpts) >= 3 and segmonto_type(region):
            items.append({
                "id": base + region.get("id"),
                "type": "Annotation",
                "motivation": "classifying",
                "body": [tag_body(segmonto_type(region)), xml_link(xml_iri, "TextRegion", region.get("id"))],
                "target": {"source": source, "selector": selectors(rpts)},
            })
        for line in children(region, "TextLine"):
            lpts = points(line)
            equiv = first(line, "TextEquiv")
            uni = first(equiv, "Unicode") if equiv is not None else None
            text = (uni.text or "") if uni is not None else ""
            if len(lpts) < 3:
                continue
            body = [{"type": "TextualBody", "value": text, "format": "text/plain"}]
            if segmonto_type(line):
                body.append(tag_body(segmonto_type(line)))
            body.append(xml_link(xml_iri, "TextLine", line.get("id")))
            items.append({
                "id": base + line.get("id"),
                "type": "Annotation",
                "motivation": "describing",
                "creator": TRANSCRIBER,
                "generator": GENERATOR,
                "body": body,
                "target": {"source": source, "selector": selectors(lpts)},
            })
    return {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "id": f"{NS}AnnotationPage_{stem}",
        "type": "AnnotationPage",
        "items": items,
    }


def dataverse_links(instances_path):
    """Charter id -> (JPEG IRI, PageXML IRI) from the instances file."""
    data = json.load(open(instances_path))
    out = {}
    for node in data.get("@graph", []):
        if node.get("ddi-cdi:content"):
            out[node["ddi-cdi:content"]] = (
                node.get("amsmb:hasPhysicalInstance", {}).get("@id"),
                node.get("amsmb:hasLogicalAnnotation", {}).get("@id"),
            )
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("out_dir")
    ap.add_argument("xml", nargs="+")
    ap.add_argument("--instances", help="amsmb_charters_instances.jsonld, to use Dataverse image and PageXML IRIs")
    a = ap.parse_args()
    links = dataverse_links(a.instances) if a.instances else {}
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for x in a.xml:
        page = convert(x, *links.get(Path(x).stem, (None, None)))
        dest = out / (Path(x).stem + ".annotations.jsonld")
        dest.write_text(json.dumps(page, ensure_ascii=False, indent=2))
        print(f"{x} -> {dest} ({len(page['items'])} annotations)", file=sys.stderr)


if __name__ == "__main__":
    main()
