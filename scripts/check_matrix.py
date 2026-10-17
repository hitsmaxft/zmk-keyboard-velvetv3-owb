#!/usr/bin/env python3
"""Check all 46 transform positions, GPIO pins, and optional source EDA nets."""

import argparse
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHIELD = ROOT / "boards/shields/velvetv3_owb"
EXPECTED_ROWS = [12, 12, 12, 10]
ROW_PINS = [(0, 24), (1, 0), (0, 11), (1, 4)]
LEFT_COLS = [(0, 2), (1, 15), (1, 13), (1, 11), (0, 10), (0, 9)]
RIGHT_COLS = list(reversed(LEFT_COLS))


def check_gpio(path: Path, expected_cols: list[tuple[int, int]]) -> None:
    source = (SHIELD / "velvetv3_owb_kscan.dtsi").read_text() + path.read_text()
    row_text = source.split("row-gpios =", 1)[1].split(";", 1)[0]
    col_text = source.split("col-gpios =", 1)[1].split(";", 1)[0]
    pattern = r"<&gpio([01])\s+(\d+)\s+"
    rows = [(int(a), int(b)) for a, b in re.findall(pattern, row_text)]
    cols = [(int(a), int(b)) for a, b in re.findall(pattern, col_text)]
    assert rows == ROW_PINS, (path, "rows", rows)
    assert cols == expected_cols, (path, "columns", cols)
    assert len(set(rows + cols)) == 10, (path, "reused GPIO")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eda", type=Path, help="optional private EDA native JSON capture")
    args = parser.parse_args()
    with (ROOT / "docs/matrix-map.csv").open(newline="") as file:
        matrix = list(csv.DictReader(file))
    assert len(matrix) == 46
    assert [int(p["position"]) for p in matrix] == list(range(46))
    assert len(set(p["switch"] for p in matrix)) == 46
    assert [sum(int(p["physical_row"]) == r for p in matrix) for r in range(1, 5)] == EXPECTED_ROWS

    source = (SHIELD / "velvetv3_owb.dtsi").read_text()
    map_text = source.split("map = <", 1)[1].split(">;", 1)[0]
    map_text = re.sub(r"//[^\n]*", "", map_text)
    positions = [(int(r), int(c)) for r, c in re.findall(r"RC\((\d+),\s*(\d+)\)", map_text)]
    assert len(positions) == 46
    assert len(set(positions)) == 46
    for record, (row, col) in zip(matrix, positions):
        assert row + 1 == int(record["physical_row"]), record
        side = record["side"]
        assert side == ("L" if col < 6 else "R"), record
        assert col % 6 + 1 == int(record["col_net"][1]), record
        assert record["row_net"] == f"R{row+1}{side}", record
    # The first thumb key on either half is physical R4C1, but electrical C5.
    assert matrix[40]["col_net"] == "C5L"
    assert matrix[41]["col_net"] == "C5R"
    assert positions[40] == (3, 4) and positions[41] == (3, 10)

    check_gpio(SHIELD / "velvetv3_owb_left_kscan.dtsi", LEFT_COLS)
    check_gpio(SHIELD / "velvetv3_owb_right.overlay", RIGHT_COLS)
    right = (SHIELD / "velvetv3_owb_right.overlay").read_text()
    assert "col-offset = <6>" in right

    dya = {
        line for line in (ROOT / "config/velvetv3_owb_dya.conf").read_text().splitlines()
        if line and not line.startswith("#")
    }
    for name in ("velvetv3_owb_left", "velvetv3_owb_dongle_adapter"):
        folder = SHIELD if name.endswith("_left") else SHIELD.parent / name
        actual = set((folder / f"{name}.conf").read_text().splitlines())
        assert dya <= actual, f"{name} has drifted from shared DYA Studio options"
    for name in ("velvetv3_owb_ph_left", "velvetv3_owb_right"):
        actual = (SHIELD / f"{name}.conf").read_text()
        assert "CONFIG_ZMK_STUDIO=n" in actual
        assert "CONFIG_ZMK_SETTINGS_RPC=y" in actual

    layout = (SHIELD / "velvetv3_owb-layouts.dtsi").read_text()
    layout_keys = re.findall(r"<&key_physical_attrs\s+100\s+100\s+([^>]+)>\s*//\s*(K\d+)\s+(\S+)/(\S+)", layout)
    assert len(layout_keys) == 46
    for record, (attributes, switch, column, row) in zip(matrix, layout_keys):
        values = [int(value.strip("()")) for value in attributes.split()]
        x, y, angle = (int(record[name]) for name in ("x_centi_u", "y_centi_u", "rotation_centi_deg"))
        assert (switch, column, row) == (record["switch"], record["col_net"], record["row_net"])
        assert values == [x, y, angle, x + 50, y + 50], (switch, values)

    if args.eda:
        board = json.loads(args.eda.read_text())
        components = board["components"]
        row_for_intermediate = {}
        for name, component in components.items():
            if not re.fullmatch(r"D\d+", name):
                continue
            nets = set(component.get("nets", {}).values())
            rows = [net for net in nets if re.fullmatch(r"R[1-4][LR]", net)]
            internal = [net for net in nets if net.startswith("$")]
            if len(rows) == len(internal) == 1:
                row_for_intermediate[internal[0]] = rows[0]
        for record in matrix:
            component = components[record["switch"]]
            nets = component["nets"]
            assert nets["e3112-e2"] == record["col_net"], record
            assert row_for_intermediate[nets["e3112-e3"]] == record["row_net"], record
            reference = components["K1"]["location"]
            position = component["location"]
            expected_x = round((position[0] - reference[0]) * 100 / 19.05)
            assert int(record["x_centi_u"]) == expected_x, record
            expected_y = round((reference[1] - position[1]) * 100 / 19.05 + int(matrix[0]["y_centi_u"]))
            assert int(record["y_centi_u"]) == expected_y, record
            assert int(record["rotation_centi_deg"]) == round((180 - component["rotation"]) * 100), record
    print("OK: 46 physical coordinates, 46 unique RC cells, both GPIO maps, and thumb C5 correction")


if __name__ == "__main__":
    main()
