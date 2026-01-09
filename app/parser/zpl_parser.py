import re
from typing import List
from app.models.label import Label


class ZPLParseError(Exception):
    """Raised when ZPL parsing fails"""
    pass


class ZPLParser:
    """Parse ZPL (Zebra Programming Language) commands and extract label data"""

    # Regex patterns for ZPL commands
    LABEL_BLOCK = r'\^XA.*?\^XZ'
    BARCODE_PATTERN = r'\^BCN,\d+,N,N\^FD([A-Z0-9]+)\^FS'
    PRODUCT_NAME_PATTERN = r'\^FO22,115.*?\^FD(.*?)\^FS'
    COLOR_PATTERN = r'\^FO22,150.*?\^FD(.*?)\^FS'
    SKU_PATTERN = r'\^FO22,170.*?\^FDSKU:\s*([A-Z0-9]+)\^FS'
    QUANTITY_PATTERN = r'\^PQ(\d+)'
    HEX_CHAR_PATTERN = r'_([0-9A-F]{2})'

    def parse_file(self, file_path: str) -> List[Label]:
        """
        Parse entire ZPL file and return list of labels

        Args:
            file_path: Path to ZPL text file

        Returns:
            List of Label objects

        Raises:
            ZPLParseError: If file cannot be parsed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ZPLParseError(f"Failed to read file: {e}")

        # Extract individual label blocks
        label_blocks = self._extract_label_blocks(content)

        if not label_blocks:
            raise ZPLParseError("No valid label blocks found (^XA...^XZ)")

        # Parse each label block
        labels = []
        for i, block in enumerate(label_blocks, 1):
            try:
                label = self._parse_single_label(block)
                labels.append(label)
            except Exception as e:
                # Continue parsing other labels even if one fails
                print(f"Warning: Failed to parse label {i}: {e}")
                continue

        if not labels:
            raise ZPLParseError("No valid labels could be parsed")

        return labels

    def _extract_label_blocks(self, text: str) -> List[str]:
        """
        Split text into individual label blocks (^XA...^XZ)

        Args:
            text: Full ZPL file content

        Returns:
            List of label block strings
        """
        matches = re.findall(self.LABEL_BLOCK, text, re.DOTALL)
        return matches

    def _parse_single_label(self, block: str) -> Label:
        """
        Extract data from a single label block

        Args:
            block: Single ZPL label block string

        Returns:
            Label object with extracted data

        Raises:
            ZPLParseError: If required fields are missing
        """
        # Extract barcode
        barcode = self._extract_barcode(block)
        if not barcode:
            raise ZPLParseError("Missing barcode data")

        # Extract product name
        product_name = self._extract_text_field(block, self.PRODUCT_NAME_PATTERN)
        if not product_name:
            raise ZPLParseError("Missing product name")

        # Decode special characters in product name
        product_name = self._decode_special_chars(product_name)

        # Extract color (optional)
        color = self._extract_text_field(block, self.COLOR_PATTERN)
        if color:
            color = self._decode_special_chars(color)

        # Extract SKU
        sku = self._extract_sku(block)
        if not sku:
            raise ZPLParseError("Missing SKU")

        # Extract quantity
        quantity = self._extract_quantity(block)

        # Validate quantity
        if quantity > 10000:
            raise ZPLParseError(f"Quantity {quantity} exceeds maximum (10000)")

        return Label(
            barcode=barcode,
            product_name=product_name,
            color=color if color else None,
            sku=sku,
            quantity=quantity
        )

    def _extract_barcode(self, block: str) -> str:
        """
        Extract barcode data from ^BCN command

        Args:
            block: ZPL label block

        Returns:
            Barcode value or empty string
        """
        match = re.search(self.BARCODE_PATTERN, block)
        return match.group(1) if match else ""

    def _extract_text_field(self, block: str, pattern: str) -> str:
        """
        Extract text from ^FD...^FS pattern

        Args:
            block: ZPL label block
            pattern: Regex pattern to match

        Returns:
            Extracted text or empty string
        """
        match = re.search(pattern, block)
        return match.group(1).strip() if match else ""

    def _extract_sku(self, block: str) -> str:
        """
        Extract SKU from label

        Args:
            block: ZPL label block

        Returns:
            SKU value or empty string
        """
        match = re.search(self.SKU_PATTERN, block)
        return match.group(1) if match else ""

    def _extract_quantity(self, block: str) -> int:
        """
        Extract quantity from ^PQ command

        Args:
            block: ZPL label block

        Returns:
            Quantity value (default: 1)
        """
        match = re.search(self.QUANTITY_PATTERN, block)
        return int(match.group(1)) if match else 1

    def _decode_special_chars(self, text: str) -> str:
        """
        Decode ZPL hex encoding (_C3_B3 -> ó)

        ZPL uses _XX format for hex-encoded UTF-8 bytes

        Args:
            text: Text with hex-encoded characters

        Returns:
            Decoded UTF-8 text
        """
        def replace_hex(match):
            hex_value = match.group(1)
            try:
                # Convert hex to byte
                byte_val = bytes.fromhex(hex_value)
                return byte_val.decode('latin-1')  # Decode individual byte
            except Exception:
                return match.group(0)  # Return original if decoding fails

        # Replace all _XX patterns
        decoded = re.sub(self.HEX_CHAR_PATTERN, replace_hex, text)

        # Handle multi-byte UTF-8 sequences (e.g., _C3_B3 for ó)
        # First, extract all hex bytes in sequence
        hex_sequence = re.findall(self.HEX_CHAR_PATTERN, text)
        if len(hex_sequence) >= 2:
            try:
                # Reconstruct the full hex sequence
                hex_bytes = bytes.fromhex(''.join(hex_sequence))
                # Try to decode as UTF-8
                decoded_utf8 = hex_bytes.decode('utf-8')
                # Replace the entire sequence in the original text
                original_sequence = '_' + '_'.join(hex_sequence)
                decoded = text.replace(original_sequence, decoded_utf8)
            except Exception:
                pass  # Fall back to single-byte decoding

        return decoded
