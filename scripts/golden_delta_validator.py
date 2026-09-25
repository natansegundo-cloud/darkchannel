#!/usr/bin/env python3
"""Valida herança estrutural exata contra Golden Layout Snapshots."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "config" / "golden_layout_snapshots.json"
POC_STATUS = ROOT / "tests" / "art_direction_poc_v2" / "status.json"
TEXT_TYPES = {"hero_number", "hero_word", "headline", "label", "micro_label"}
REQUIRED_FIELDS = {
    "semantic_id", "type", "x", "y", "width", "height", "font_size",
    "font_weight", "align", "rotation", "opacity", "z_layer",
}


class GoldenDeltaError(RuntimeError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_text(element: dict[str, Any]) -> bool:
    return element.get("type") in TEXT_TYPES or element.get("font_size") is not None


def boxes_overlap(first: dict[str, Any], second: dict[str, Any]) -> bool:
    return (
        first["x"] < second["x"] + second["width"]
        and first["x"] + first["width"] > second["x"]
        and first["y"] < second["y"] + second["height"]
        and first["y"] + first["height"] > second["y"]
    )


def validate_global_prohibitions(reference: dict[str, Any], elements: list[dict[str, Any]]) -> None:
    exceptions = set(reference.get("authorized_exceptions", []))
    canvas_width, canvas_height = reference["canvas"]
    texts = [item for item in elements if is_text(item) and float(item.get("opacity", 1)) >= 0.12]

    for element in texts:
        if float(element.get("rotation", 0)) != 0:
            raise GoldenDeltaError("TEXT_ROTATION_FORBIDDEN", element["semantic_id"])
        outside = (
            element["x"] < 0 or element["y"] < 0
            or element["x"] + element["width"] > canvas_width
            or element["y"] + element["height"] > canvas_height
        )
        if outside and not (
            element.get("dominant") and "dominant_text_crop" in exceptions
        ) and not (
            element["semantic_id"] == "hero_shadow" and "paired_hero_shadow" in exceptions
        ):
            raise GoldenDeltaError("TEXT_OUTSIDE_CANVAS", element["semantic_id"])

    repeated: dict[str, list[str]] = {}
    for element in texts:
        content = element.get("text_content")
        if content:
            repeated.setdefault(content, []).append(element["semantic_id"])
    duplicates = {text: ids for text, ids in repeated.items() if len(ids) > 1}
    if duplicates and not (
        "paired_hero_shadow" in exceptions
        or "paired_semantic_label_repetition" in exceptions
    ):
        raise GoldenDeltaError("DECORATIVE_HEADLINE_REPETITION", str(duplicates))

    for index, first in enumerate(texts):
        for second in texts[index + 1:]:
            if not boxes_overlap(first, second):
                continue
            pair = {first["semantic_id"], second["semantic_id"]}
            if pair == {"hero_shadow", "hero_value"} and "paired_hero_shadow" in exceptions:
                continue
            raise GoldenDeltaError(
                "TEXT_TEXT_OVERLAP",
                f"{first['semantic_id']} x {second['semantic_id']}",
            )


def validate_reference(reference: dict[str, Any]) -> None:
    if reference.get("canvas") != [1920, 1080]:
        raise GoldenDeltaError("INVALID_GOLDEN_CANVAS", reference["reference_id"])
    source = ROOT / reference["source_asset"]
    if not source.is_file():
        raise GoldenDeltaError("MISSING_GOLDEN_SOURCE", reference["source_asset"])
    if sha256(source) != reference["source_sha256"]:
        raise GoldenDeltaError("GOLDEN_SOURCE_HASH_MISMATCH", reference["reference_id"])
    elements = reference.get("elements", [])
    semantic_ids = [item.get("semantic_id") for item in elements]
    if not elements or len(semantic_ids) != len(set(semantic_ids)):
        raise GoldenDeltaError("INVALID_GOLDEN_ELEMENT_SET", reference["reference_id"])
    for element in elements:
        missing = sorted(REQUIRED_FIELDS - set(element))
        if missing:
            raise GoldenDeltaError(
                "INVALID_GOLDEN_ELEMENT",
                f"{reference['reference_id']}:{element.get('semantic_id')} missing {missing}",
            )
    validate_global_prohibitions(reference, elements)


def validate_scene(scene: dict[str, Any], catalog: dict[str, Any]) -> None:
    reference_id = scene.get("inherits_from")
    references = {item["reference_id"]: item for item in catalog["snapshots"]}
    if reference_id not in references:
        raise GoldenDeltaError("UNKNOWN_GOLDEN_REFERENCE", str(reference_id))
    reference = references[reference_id]
    if scene.get("canvas") != reference["canvas"]:
        raise GoldenDeltaError("UNAUTHORIZED_GOLDEN_DELTA", "canvas")

    golden_by_id = {item["semantic_id"]: item for item in reference["elements"]}
    scene_by_id = {item.get("semantic_id"): item for item in scene.get("elements", [])}
    if set(scene_by_id) != set(golden_by_id):
        raise GoldenDeltaError("UNAUTHORIZED_GOLDEN_DELTA", "element_set")

    allowed = set(reference.get("allowed_deltas", []))
    for semantic_id, golden in golden_by_id.items():
        candidate = scene_by_id[semantic_id]
        all_fields = set(golden) | set(candidate)
        for field in sorted(all_fields):
            if field in allowed:
                continue
            if golden.get(field) != candidate.get(field):
                raise GoldenDeltaError(
                    "UNAUTHORIZED_GOLDEN_DELTA",
                    f"{semantic_id}.{field}: {golden.get(field)!r} -> {candidate.get(field)!r}",
                )
    validate_global_prohibitions(reference, list(scene_by_id.values()))


def self_test(catalog: dict[str, Any]) -> None:
    references = catalog.get("snapshots", [])
    if len(references) != 7:
        raise GoldenDeltaError("INVALID_GOLDEN_COUNT", str(len(references)))
    ids = [item["reference_id"] for item in references]
    if len(ids) != len(set(ids)):
        raise GoldenDeltaError("DUPLICATE_GOLDEN_REFERENCE", str(ids))
    for reference in references:
        validate_reference(reference)
        exact_scene = {
            "inherits_from": reference["reference_id"],
            "canvas": copy.deepcopy(reference["canvas"]),
            "elements": copy.deepcopy(reference["elements"]),
        }
        validate_scene(exact_scene, catalog)

    negative = {
        "inherits_from": references[1]["reference_id"],
        "canvas": copy.deepcopy(references[1]["canvas"]),
        "elements": copy.deepcopy(references[1]["elements"]),
    }
    negative["elements"][0]["x"] += 1
    try:
        validate_scene(negative, catalog)
    except GoldenDeltaError as exc:
        if exc.code != "UNAUTHORIZED_GOLDEN_DELTA":
            raise
    else:
        raise GoldenDeltaError("NEGATIVE_TEST_FAILED", "unauthorized x delta was accepted")

    status = read_json(POC_STATUS)
    if status.get("status") != "REJECTED" or status.get("reason") != "UNCONTROLLED_LAYOUT_REINTERPRETATION":
        raise GoldenDeltaError("POC_REJECTION_STATUS_INVALID", str(status))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scene", type=Path, help="JSON de cena com inherits_from e elements.")
    args = parser.parse_args()
    catalog = read_json(SNAPSHOTS)
    self_test(catalog)
    if args.scene:
        validate_scene(read_json(args.scene), catalog)
        print(f"SCENE={args.scene}")
    print(f"GOLDEN_SNAPSHOTS={len(catalog['snapshots'])}")
    print("NEGATIVE_UNAUTHORIZED_DELTA=REJECTED")
    print("DELTA_VALIDATOR=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (GoldenDeltaError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        raise SystemExit(2)
