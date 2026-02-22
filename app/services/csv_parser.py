"""
CSV Parser — Product Catalog Import
Validates and parses CSV files into ProductCreate objects.
Required columns: sku_id, product_name, description
Optional columns: image_url, sku_tier, category
"""

import csv
import io
import logging

from app.models.campaign_schemas import ProductCreate

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {"sku_id", "product_name", "description"}
OPTIONAL_COLUMNS = {"image_url", "sku_tier", "category"}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS

# Normalize sku_tier values
_TIER_MAP = {
    "hero": "hero",
    "premium": "hero",
    "top": "hero",
    "catalog": "catalog",
    "standard": "catalog",
    "basic": "catalog",
}


def parse_csv(text: str) -> tuple[list[ProductCreate], list[str]]:
    """Parse CSV text into validated ProductCreate objects.
    Returns (products, errors) — partial success is allowed.
    """
    products: list[ProductCreate] = []
    errors: list[str] = []

    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        return [], ["CSV file is empty or has no header row"]

    # Normalize column names (strip whitespace, lowercase)
    headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        return [], [f"Missing required columns: {', '.join(sorted(missing))}"]

    for row_num, row in enumerate(reader, start=2):  # row 1 is header
        # Normalize keys
        row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}

        # Validate required fields are non-empty
        empty_fields = [col for col in REQUIRED_COLUMNS if not row.get(col)]
        if empty_fields:
            errors.append(
                f"Row {row_num}: empty required fields: {', '.join(empty_fields)}"
            )
            continue

        # Normalize sku_tier
        raw_tier = row.get("sku_tier", "catalog").lower()
        sku_tier = _TIER_MAP.get(raw_tier, "catalog")

        try:
            product = ProductCreate(
                sku_id=row["sku_id"],
                product_name=row["product_name"],
                description=row["description"],
                image_url=row.get("image_url") or None,
                sku_tier=sku_tier,
                category=row.get("category") or None,
            )
            products.append(product)
        except Exception as e:
            errors.append(f"Row {row_num}: {e}")

    logger.info("CSV parsed: %d products, %d errors", len(products), len(errors))
    return products, errors
