"""Tests for the CSV product catalog parser."""
import pytest

from app.services.csv_parser import parse_csv


class TestCSVParser:
    """Verify CSV parsing, validation, and tier normalization."""

    VALID_CSV = (
        "sku_id,product_name,description,sku_tier\n"
        "SKU-001,Widget,A great widget,hero\n"
        "SKU-002,Gadget,A cool gadget,catalog\n"
    )

    def test_valid_csv_returns_products(self):
        products, errors = parse_csv(self.VALID_CSV)
        assert len(products) == 2
        assert len(errors) == 0
        assert products[0].sku_id == "SKU-001"
        assert products[1].product_name == "Gadget"

    def test_missing_required_columns(self):
        csv_text = "sku_id,product_name\nSKU-001,Widget\n"
        products, errors = parse_csv(csv_text)
        assert len(products) == 0
        assert len(errors) == 1
        assert "description" in errors[0].lower()

    def test_empty_csv(self):
        products, errors = parse_csv("")
        assert len(products) == 0
        assert len(errors) == 1

    def test_tier_normalization_premium_to_hero(self):
        csv_text = (
            "sku_id,product_name,description,sku_tier\n"
            "SKU-001,Widget,A great widget,premium\n"
        )
        products, _ = parse_csv(csv_text)
        assert products[0].sku_tier == "hero"

    def test_tier_normalization_standard_to_catalog(self):
        csv_text = (
            "sku_id,product_name,description,sku_tier\n"
            "SKU-001,Widget,A great widget,standard\n"
        )
        products, _ = parse_csv(csv_text)
        assert products[0].sku_tier == "catalog"

    def test_tier_default_to_catalog(self):
        csv_text = (
            "sku_id,product_name,description\n"
            "SKU-001,Widget,A great widget\n"
        )
        products, _ = parse_csv(csv_text)
        assert products[0].sku_tier == "catalog"

    def test_empty_required_field_skipped(self):
        csv_text = (
            "sku_id,product_name,description\n"
            "SKU-001,,A widget with no name\n"
            "SKU-002,Valid,A valid product\n"
        )
        products, errors = parse_csv(csv_text)
        assert len(products) == 1
        assert len(errors) == 1
        assert products[0].sku_id == "SKU-002"

    def test_whitespace_in_headers_handled(self):
        csv_text = (
            " sku_id , product_name , description \n"
            "SKU-001,Widget,A great widget\n"
        )
        products, errors = parse_csv(csv_text)
        assert len(products) == 1
        assert len(errors) == 0
