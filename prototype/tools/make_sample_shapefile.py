from __future__ import annotations

import csv
import datetime as dt
import os
import struct
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "downloads"
CSV_PATH = DOWNLOADS / "sample-products.csv"
OUT_DIR = DOWNLOADS / "sample_resource_sites_shp"
ZIP_PATH = DOWNLOADS / "sample-resource-sites-shapefile.zip"


def be_i32(value: int) -> bytes:
    return struct.pack(">i", value)


def le_i32(value: int) -> bytes:
    return struct.pack("<i", value)


def le_f64(value: float) -> bytes:
    return struct.pack("<d", value)


def shp_header(file_length_words: int, xmin: float, ymin: float, xmax: float, ymax: float) -> bytes:
    header = bytearray()
    header += be_i32(9994)
    header += b"\x00" * 20
    header += be_i32(file_length_words)
    header += le_i32(1000)
    header += le_i32(1)
    header += le_f64(xmin)
    header += le_f64(ymin)
    header += le_f64(xmax)
    header += le_f64(ymax)
    header += le_f64(0)
    header += le_f64(0)
    header += le_f64(0)
    header += le_f64(0)
    return bytes(header)


def read_points() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_shp(points: list[dict[str, str]]) -> None:
    coords = [(float(row["longitude"]), float(row["latitude"])) for row in points]
    xmin = min(x for x, _ in coords)
    xmax = max(x for x, _ in coords)
    ymin = min(y for _, y in coords)
    ymax = max(y for _, y in coords)

    records = []
    shx_records = []
    offset_words = 50
    for index, (x, y) in enumerate(coords, start=1):
        content = le_i32(1) + le_f64(x) + le_f64(y)
        records.append(be_i32(index) + be_i32(len(content) // 2) + content)
        shx_records.append(be_i32(offset_words) + be_i32(len(content) // 2))
        offset_words += (8 + len(content)) // 2

    shp_bytes = shp_header(offset_words, xmin, ymin, xmax, ymax) + b"".join(records)
    shx_length_words = 50 + len(points) * 4
    shx_bytes = shp_header(shx_length_words, xmin, ymin, xmax, ymax) + b"".join(shx_records)

    (OUT_DIR / "sample_resource_sites.shp").write_bytes(shp_bytes)
    (OUT_DIR / "sample_resource_sites.shx").write_bytes(shx_bytes)


def dbf_field(name: str, kind: str, length: int, decimals: int = 0) -> bytes:
    data = bytearray(32)
    encoded = name.encode("ascii")[:10]
    data[: len(encoded)] = encoded
    data[11] = ord(kind)
    data[16] = length
    data[17] = decimals
    return bytes(data)


def fit(value: str, length: int) -> bytes:
    return value.encode("ascii", errors="ignore")[:length].ljust(length, b" ")


def write_dbf(points: list[dict[str, str]]) -> None:
    fields = [
        ("SITE_ID", "C", 12),
        ("GROUP_NAME", "C", 48),
        ("DZONGKHAG", "C", 24),
        ("PRODUCT", "C", 32),
        ("STATUS", "C", 12),
    ]
    record_length = 1 + sum(field[2] for field in fields)
    header_length = 32 + len(fields) * 32 + 1
    today = dt.date.today()

    header = bytearray(32)
    header[0] = 3
    header[1] = today.year - 1900
    header[2] = today.month
    header[3] = today.day
    header[4:8] = struct.pack("<I", len(points))
    header[8:10] = struct.pack("<H", header_length)
    header[10:12] = struct.pack("<H", record_length)

    body = bytearray(header)
    for field in fields:
        body += dbf_field(*field)
    body += b"\r"

    for index, row in enumerate(points, start=1):
        body += b" "
        body += fit(row["product_id"], 12)
        body += fit(row["group_name"], 48)
        body += fit(row["dzongkhag"], 24)
        body += fit(row["product_name"], 32)
        body += fit(row["status"], 12)
    body += b"\x1a"
    (OUT_DIR / "sample_resource_sites.dbf").write_bytes(bytes(body))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    points = read_points()
    write_shp(points)
    write_dbf(points)
    (OUT_DIR / "sample_resource_sites.prj").write_text(
        'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],'
        'PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]\n',
        encoding="ascii",
    )
    (OUT_DIR / "sample_resource_sites.cpg").write_text("UTF-8\n", encoding="ascii")

    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUT_DIR.iterdir()):
            archive.write(path, arcname=path.name)

    print(ZIP_PATH)


if __name__ == "__main__":
    main()
