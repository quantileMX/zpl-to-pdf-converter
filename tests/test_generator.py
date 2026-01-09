"""
Unit tests for PDF generator
"""

import pytest
import tempfile
import os
from app.generator.pdf_generator import PDFGenerator, PDFGenerationError
from app.models.label import Label


def test_expand_labels_by_quantity():
    """Test label expansion based on quantity"""
    generator = PDFGenerator()

    labels = [
        Label(barcode="TEST1", product_name="Product 1", sku="SKU1", quantity=3),
        Label(barcode="TEST2", product_name="Product 2", sku="SKU2", quantity=2),
    ]

    expanded = generator._expand_labels_by_quantity(labels)

    assert len(expanded) == 5  # 3 + 2
    assert expanded[0].barcode == "TEST1"
    assert expanded[3].barcode == "TEST2"


def test_calculate_label_position():
    """Test label position calculation"""
    generator = PDFGenerator()

    # First label (top-left)
    x0, y0 = generator._calculate_label_position(0)
    assert x0 > 0
    assert y0 > 0

    # Second label (top-right)
    x1, y1 = generator._calculate_label_position(1)
    assert x1 > x0  # Should be to the right

    # 11th label should be on second page (position 0 on new page)
    x10, y10 = generator._calculate_label_position(10)
    assert x10 == x0  # Same x as first label


def test_generate_pdf():
    """Test PDF generation"""
    generator = PDFGenerator()

    labels = [
        Label(
            barcode="TEST12345",
            product_name="Test Product",
            sku="TEST001",
            quantity=2,
            color="Blue"
        )
    ]

    # Create temp output file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        output_path = tmp.name

    try:
        result = generator.generate_pdf(labels, output_path)

        # Check file was created
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
        assert result == output_path

    finally:
        # Clean up
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_generate_pdf_empty_labels():
    """Test error handling for empty labels"""
    generator = PDFGenerator()

    with pytest.raises(PDFGenerationError):
        generator.generate_pdf([], "output.pdf")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
