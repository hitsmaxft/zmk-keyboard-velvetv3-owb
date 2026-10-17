#!/usr/bin/env python3
"""Generate ZMK physical positions and review SVG from one EDA-derived table."""

import argparse
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/matrix-map.csv"
DESTINATION = ROOT / "docs/layout.svg"
LAYOUT_DTSI = ROOT / "boards/shields/velvetv3_owb/velvetv3_owb-layouts.dtsi"


def render(records: list[dict[str, str]]) -> str:
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 650" role="img" aria-label="Velvet V3 OWB 46-key physical layout and electrical matrix">',
        '<rect x="0" y="0" width="1600" height="650" fill="#111827"/>',
        '<text x="40" y="35" fill="#f9fafb" font-family="Arial,sans-serif" font-size="25">Velvet V3 OWB · 46 keys</text>',
        '<text x="40" y="57" fill="#9ca3af" font-family="Arial,sans-serif" font-size="14">EDA switch centers · labels show electrical ROW/COL · gold: physical R4C1, electrical C5</text>',
    ]
    for position in records:
        center_x = int(position["x_centi_u"]) + 90
        center_y = int(position["y_centi_u"]) + 100
        angle = math.radians(int(position["rotation_centi_deg"]) / 100)
        special = position["position"] in ("40", "41")
        fill = "#d97706" if special else ("#2563eb" if position["side"] == "L" else "#059669")
        label = f'{position["row_net"][:-1]}{position["col_net"][:-1]}'
        corners = []
        for dx, dy in ((-44, -44), (44, -44), (44, 44), (-44, 44)):
            x = center_x + dx * math.cos(angle) - dy * math.sin(angle)
            y = center_y + dx * math.sin(angle) + dy * math.cos(angle)
            corners.append(f"{x:.1f},{y:.1f}")
        lines.append(
            f'<polygon points="{" ".join(corners)}" fill="{fill}" '
            'stroke="#e5e7eb" stroke-width="2" stroke-linejoin="round"/>'
        )
        lines.append(
            f'<text x="{center_x}" y="{center_y-6}" text-anchor="middle" '
            f'fill="white" font-family="Arial,sans-serif" font-size="16" font-weight="bold">{label}</text>'
        )
        lines.append(
            f'<text x="{center_x}" y="{center_y+17}" text-anchor="middle" '
            f'fill="#e5e7eb" font-family="Arial,sans-serif" font-size="12">{position["switch"]}</text>'
        )
    return "\n".join([*lines, "</svg>", ""])


def render_dtsi(records: list[dict[str, str]]) -> str:
    lines = [
        "#include <physical_layouts.dtsi>",
        "/ {",
        "    velvetv3_owb_layout: velvetv3_owb_layout {",
        '        compatible = "zmk,physical-layout";',
        '        display-name = "Velvet V3 OWB 46";',
        "        transform = <&velvetv3_owb_transform>;",
        "        keys =",
    ]
    for index, position in enumerate(records):
        x = int(position["x_centi_u"])
        y = int(position["y_centi_u"])
        angle = int(position["rotation_centi_deg"])
        angle_text = f"({angle})" if angle < 0 else str(angle)
        prefix = "              " if index == 0 else "            , "
        lines.append(
            f"{prefix}<&key_physical_attrs 100 100 {x} {y} {angle_text} {x+50} {y+50}> "
            f"// {position['switch']} {position['col_net']}/{position['row_net']}"
        )
    return "\n".join([*lines, "        ;", "    };", "};", ""])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the checked-in SVG is stale")
    args = parser.parse_args()
    with SOURCE.open(newline="") as file:
        records = list(csv.DictReader(file))
    assert len(records) == 46
    content = render(records)
    dtsi = render_dtsi(records)
    if args.check:
        assert DESTINATION.read_text() == content, "docs/layout.svg is stale"
        assert LAYOUT_DTSI.read_text() == dtsi, "ZMK physical layout DTSI is stale"
        print("OK: SVG and ZMK physical layout both match all 46 CSV positions")
    else:
        DESTINATION.write_text(content)
        LAYOUT_DTSI.write_text(dtsi)
