from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128
from reportlab.graphics import renderPDF
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import List
import re # Essential for fixing the _C3_B3 accent issue

from app.models.label import Label


class PDFGenerationError(Exception):
    """Raised when PDF generation fails"""
    pass


class PDFGenerator:
    """Generate PDF from parsed ZPL labels - thermal label format"""

    # Thermal label size (2" x 1" - standard thermal label)
    PAGE_WIDTH = 2 * inch  # 288 points
    PAGE_HEIGHT = 1 * inch  # 144 points

    # Margins for thermal label
    MARGIN_LEFT = 0.1 * inch
    MARGIN_RIGHT = 0.1 * inch
    MARGIN_TOP = 0.1 * inch

    def __init__(self):
        """Initialize PDF generator"""
        # Register DejaVuSans fonts for proper Unicode support (accented characters)
        try:
            pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
            self.font_regular = 'DejaVuSans'
            self.font_bold = 'DejaVuSans-Bold'
        except Exception:
            # Fallback to Helvetica if DejaVu fonts not available
            self.font_regular = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def _decode_zpl_text(self, text: str) -> str:
        """Converts ZPL hex codes like _C3_B3 into actual characters"""
        if not text:
            return ""
        try:
            # Match consecutive hex codes like _C3_B3 and decode as a complete UTF-8 sequence
            def decode_hex_sequence(match):
                hex_str = ''.join(match.group(0).split('_')[1:])  # Extract all hex bytes
                return bytes.fromhex(hex_str).decode('utf-8', errors='ignore')

            return re.sub(r'(?:_[0-9A-Fa-f]{2})+', decode_hex_sequence, str(text))
        except Exception:
            return str(text)

    def generate_pdf(self, labels: List[Label], output_path: str) -> str:
        """
        Generate PDF with one full-page label per product
        NOTE: Quantity is informational only (items in box), not used for duplication

        Args:
            labels: List of Label objects
            output_path: Output PDF file path

        Returns:
            Path to generated PDF file

        Raises:
            PDFGenerationError: If PDF generation fails
        """
        if not labels:
            raise PDFGenerationError("No labels to generate")
 
        try:
            # Create PDF canvas
            c = self._create_canvas(output_path)

            for i, label in enumerate(labels):
                # Draw full-page label
                self._draw_label(c, label)

                # Start new page if not the last label
                if i < len(labels) - 1:
                    c.showPage()

            # Save PDF
            c.save()

            return output_path

        except Exception as e:
            raise PDFGenerationError(f"Failed to generate PDF: {e}")

    def _create_canvas(self, output_path: str) -> canvas.Canvas:
        """Initialize PDF canvas for thermal labels"""
        # FIX: Ensure initial canvas page size is correct
        c = canvas.Canvas(output_path, pagesize=(self.PAGE_WIDTH, self.PAGE_HEIGHT))
        c.setTitle("Product Labels")
        return c

    def _draw_label(self, c: canvas.Canvas, label: Label):
        """Draw thermal label format"""
        # Calculate center X for barcode
        center_x = self.PAGE_WIDTH / 2

        # Start from top of label
        current_y = self.PAGE_HEIGHT - self.MARGIN_TOP - 0.2 * inch

        # Draw barcode at top center
        self._draw_barcode(c, label.barcode, center_x, current_y)
        current_y -= 0.12 * inch

        # Draw barcode text below barcode
        c.setFont(self.font_bold, 8)
        barcode_text_width = c.stringWidth(label.barcode, self.font_bold, 8)
        c.drawString(center_x - barcode_text_width / 2, current_y, label.barcode)
        current_y -= 0.12 * inch

        # Clean product name from hex codes like _C3_B3
        clean_name = self._decode_zpl_text(label.product_name)

        # Draw product name (wrapped)
        current_y = self._draw_text_wrapped(
            c,
            clean_name,
            self.MARGIN_LEFT,
            current_y,
            self.PAGE_WIDTH - (self.MARGIN_LEFT * 2),
            font_size=5,
            font_name=self.font_bold,
            line_spacing=7
        )
        current_y -= 0.1 * inch

        # Draw color (if present)
        if label.color:
            clean_color = self._decode_zpl_text(label.color)
            c.setFont(self.font_bold, 5)
            c.drawString(self.MARGIN_LEFT, current_y, clean_color)
            current_y -= 0.1 * inch

        # Draw SKU with decoded text and no truncation
        clean_sku = self._decode_zpl_text(label.sku)
        c.setFont(self.font_bold, 5)
        # Using drawstring here as per your original file to keep logic identical
        c.drawString(self.MARGIN_LEFT, current_y, f"SKU: {clean_sku}")

    def _draw_barcode(self, c: canvas.Canvas, value: str, center_x: float, y: float):
        """Draw Code 128 barcode centered"""
        try:
            barcode = code128.Code128(
                value,
                barWidth=0.8,
                barHeight=0.25 * inch,
                humanReadable=False
            )
            barcode_width = barcode.width
            x = center_x - (barcode_width / 2)
            barcode.drawOn(c, x, y)
        except Exception as e:
            # Fallback if barcode fails
            c.setFont(self.font_bold, 8)
            c.drawCentredString(center_x, y, f"[{value}]")

    def _draw_text_wrapped(
        self,
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        max_width: float,
        font_size: int = 5,
        font_name: str = None,
        line_spacing: int = None
    ) -> float:
        """
        Draw text with simple word wrapping and return Y position after last line
        """
        if font_name is None:
            font_name = self.font_regular

        if line_spacing is None:
            line_spacing = font_size + 2

        # FIX: Ensure characters like 'ó' are handled during font measurement
        c.setFont(font_name, font_size)

        # Simple word wrapping
        words = str(text).split()
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_width = c.stringWidth(word + " ", font_name, font_size)

            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width

        if current_line:
            lines.append(" ".join(current_line))

        # Draw lines - REMOVED the [:2] limit so SKU and descriptions show in full
        last_y = y
        for i, line in enumerate(lines):
            last_y = y - i * line_spacing
            # FIX: Convert line to unicode to prevent character skipping
            c.drawString(x, last_y, str(line))

        # Return Y position after the last line
        return last_y
