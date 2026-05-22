import csv
from pathlib import Path


def load_erp_procurement(
    path: Path, producer_id: str, month: str
) -> dict[str, float]:
    records: dict[str, float] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["producer_id"] == producer_id and row["month"] == month:
                records[row["category"]] = float(row["procured_kg"])
    return records
