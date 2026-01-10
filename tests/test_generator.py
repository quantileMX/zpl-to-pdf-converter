"""
Unit tests for PDF generator
"""

import pytest
import tempfile
import os
from app.generator.pdf_generator import PDFGenerator, PDFGenerationError
from app.models.label import Label


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
