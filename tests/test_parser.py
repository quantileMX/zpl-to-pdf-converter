"""
Unit tests for ZPL parser
"""

import pytest
from app.parser.zpl_parser import ZPLParser, ZPLParseError


def test_decode_special_chars():
    """Test hex character decoding"""
    parser = ZPLParser()

    # Test simple hex encoding
    assert "ó" in parser._decode_special_chars("Jab_C3_B3n")
    assert "é" in parser._decode_special_chars("Caf_C3_A9")

    # Test text without encoding
    assert parser._decode_special_chars("Hello") == "Hello"


def test_extract_barcode():
    """Test barcode extraction"""
    parser = ZPLParser()

    block = "^BCN,54,N,N^FDGCOI36235^FS"
    assert parser._extract_barcode(block) == "GCOI36235"

    # Test missing barcode
    block_no_barcode = "^FS"
    assert parser._extract_barcode(block_no_barcode) == ""


def test_extract_quantity():
    """Test quantity extraction"""
    parser = ZPLParser()

    # Test with quantity
    block = "^PQ48,0,1,Y^XZ"
    assert parser._extract_quantity(block) == 48

    # Test without quantity (should default to 1)
    block_no_qty = "^XZ"
    assert parser._extract_quantity(block_no_qty) == 1


def test_parse_single_label():
    """Test parsing a complete label"""
    parser = ZPLParser()

    zpl_block = """^XA
^CI28
^LH0,0
^FO65,18^BY2^BCN,54,N,N^FDTEST12345^FS
^FT150,98^A0N,22,22^FH^FDTEST12345^FS
^FO22,115^A0N,18,18^FB380,2,0,L^FH^FDTest Product Name^FS
^FO22,150^A0N,18,18^FB380,1,0,L^FH^FDRed^FS
^FO22,170^A0N,18,18^FH^FDSKU: TEST001^FS
^PQ10,0,1,Y^XZ"""

    label = parser._parse_single_label(zpl_block)

    assert label.barcode == "TEST12345"
    assert label.product_name == "Test Product Name"
    assert label.color == "Red"
    assert label.sku == "TEST001"
    assert label.quantity == 10


def test_parse_file_invalid():
    """Test parsing invalid file"""
    parser = ZPLParser()

    # Non-existent file
    with pytest.raises(ZPLParseError):
        parser.parse_file("nonexistent.txt")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
