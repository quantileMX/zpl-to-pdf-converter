from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.graphics.barcode import code128
from reportlab.graphics import renderPDF
from reportlab.lib.colors import black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import List
from app.models.label import Label


class PDFGenerationError(Exception):
    """Raised when PDF generation fails"""
    pass


class PDFGenerator:
    """Generate PDF from parsed ZPL labels"""

    # Label dimensions (thermal printer size: 4" x 2")
    LABEL_WIDTH = 4 * inch
    LABEL_HEIGHT = 2 * inch

    # Page layout (Letter size: 8.5" x 11")
    LABELS_PER_ROW = 2
    LABELS_PER_COLUMN = 5
    LABELS_PER_PAGE = LABELS_PER_ROW * LABELS_PER_COLUMN  # 10 labels per page

    # Margins
    MARGIN_X = 0.25 * inch
    MARGIN_Y = 0.25 * inch

    def __init__(self):
        """Initialize PDF generator"""
        pass

    def generate_pdf(self, labels: List[Label], output_path: str) -> str:
        """
        Generate PDF with all labels (respecting quantities)

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
            # Expand labels based on quantity
            expanded_labels = self._expand_labels_by_quantity(labels)

            # Create PDF canvas
            c = self._create_canvas(output_path)

            # Draw labels
            for i, label in enumerate(expanded_labels):
                # Calculate position
                x, y = self._calculate_label_position(i)

                # Draw the label
                self._draw_label(c, label, x, y)

                # Start new page if needed
                if (i + 1) % self.LABELS_PER_PAGE == 0 and i < len(expanded_labels) - 1:
                    c.showPage()

            # Save PDF
            c.save()

            return output_path

        except Exception as e:
            raise PDFGenerationError(f"Failed to generate PDF: {e}")

    def _create_canvas(self, output_path: str) -> canvas.Canvas:
        """
        Initialize PDF canvas

        Args:
            output_path: Output PDF file path

        Returns:
            Canvas object
        """
        c = canvas.Canvas(output_path, pagesize=letter)
        c.setTitle("Product Labels")
        c.setAuthor("ZPL to PDF Converter")
        return c

    def _expand_labels_by_quantity(self, labels: List[Label]) -> List[Label]:
        """
        Duplicate labels based on ^PQ quantity

        Args:
            labels: List of unique labels

        Returns:
            Expanded list with duplicates
        """
        expanded = []
        for label in labels:
            for _ in range(label.quantity):
                expanded.append(label)
        return expanded

    def _calculate_label_position(self, index: int) -> tuple:
        """
        Calculate X, Y position for label at given index

        Args:
            index: Label index (0-based)

        Returns:
            Tuple of (x, y) coordinates in points
        """
        page_width, page_height = letter

        # Calculate which label on the current page (0-9 for 10 labels per page)
        label_on_page = index % self.LABELS_PER_PAGE

        # Calculate grid position
        col = label_on_page % self.LABELS_PER_ROW
        row = label_on_page // self.LABELS_PER_ROW

        # Calculate coordinates (from bottom-left)
        x = self.MARGIN_X + col * (self.LABEL_WIDTH + self.MARGIN_X)
        y = page_height - self.MARGIN_Y - (row + 1) * self.LABEL_HEIGHT - row * self.MARGIN_Y

        return x, y

    def _draw_label(self, c: canvas.Canvas, label: Label, x: float, y: float):
        """
        Draw a single label at specified position

        Args:
            c: Canvas object
            label: Label data
            x: X coordinate (bottom-left)
            y: Y coordinate (bottom-left)
        """
        # Draw label border (for debugging/visibility)
        c.setStrokeColor(black)
        c.setLineWidth(0.5)
        c.rect(x, y, self.LABEL_WIDTH, self.LABEL_HEIGHT, stroke=1, fill=0)

        # Draw barcode at top of label
        barcode_x = x + 0.3 * inch
        barcode_y = y + self.LABEL_HEIGHT - 0.6 * inch
        self._draw_barcode(c, label.barcode, barcode_x, barcode_y)

        # Draw barcode text below barcode
        barcode_text_y = barcode_y - 0.25 * inch
        c.setFont("Helvetica-Bold", 10)
        c.drawString(barcode_x, barcode_text_y, label.barcode)

        # Draw product name (wrapped if needed)
        product_y = barcode_text_y - 0.5 * inch
        self._draw_text_wrapped(
            c,
            label.product_name,
            x + 0.1 * inch,
            product_y,
            self.LABEL_WIDTH - 0.2 * inch,
            font_size=9
        )

        # Draw color (if present)
        if label.color:
            color_y = product_y - 0.35 * inch
            c.setFont("Helvetica", 8)
            c.drawString(x + 0.1 * inch, color_y, label.color)

        # Draw SKU at bottom
        sku_y = y + 0.15 * inch
        c.setFont("Helvetica", 8)
        c.drawString(x + 0.1 * inch, sku_y, f"SKU: {label.sku}")

    def _draw_barcode(self, c: canvas.Canvas, value: str, x: float, y: float):
        """
        Draw Code 128 barcode

        Args:
            c: Canvas object
            value: Barcode value
            x: X coordinate
            y: Y coordinate
        """
        try:
            # Create Code 128 barcode
            barcode = code128.Code128(
                value,
                barWidth=1.2,
                barHeight=0.5 * inch,
                humanReadable=False
            )

            # Draw barcode on canvas
            barcode.drawOn(c, x, y)

        except Exception as e:
            # If barcode generation fails, draw text instead
            c.setFont("Helvetica", 8)
            c.drawString(x, y, f"[Barcode: {value}]")

    def _draw_text_wrapped(
        self,
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        max_width: float,
        font_size: int = 9
    ):
        """
        Draw text with wrapping

        Args:
            c: Canvas object
            text: Text to draw
            x: X coordinate
            y: Y coordinate (top of text block)
            max_width: Maximum width in points
            font_size: Font size
        """
        c.setFont("Helvetica", font_size)

        # Simple word wrapping
        words = text.split()
        lines = []
        current_line = []
        current_width = 0

        for word in words:
            word_width = c.stringWidth(word + " ", "Helvetica", font_size)

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

        # Draw lines (max 2 lines for product name)
        line_height = font_size + 2
        for i, line in enumerate(lines[:2]):  # Limit to 2 lines
            c.drawString(x, y - i * line_height, line)
