#!/usr/bin/env python3
"""
ZPL to PDF Converter - Command Line Tool

Convert Zebra ZPL label files to printable PDF documents.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.parser.zpl_parser import ZPLParser, ZPLParseError
from app.generator.pdf_generator import PDFGenerator, PDFGenerationError


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Convert ZPL (Zebra Programming Language) files to PDF",
        epilog="Example: python convert.py input.txt -o output.pdf"
    )
    parser.add_argument(
        'input',
        help='Input ZPL file (.txt)',
        type=str
    )
    parser.add_argument(
        '-o', '--output',
        help='Output PDF file (default: input filename with .pdf extension)',
        type=str
    )
    parser.add_argument(
        '-v', '--verbose',
        help='Verbose output',
        action='store_true'
    )

    args = parser.parse_args()

    # Validate input file
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not input_path.is_file():
        print(f"Error: Not a file: {input_path}", file=sys.stderr)
        sys.exit(1)

    # Generate output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = input_path.with_suffix('.pdf')

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"Input:  {input_path}")
        print(f"Output: {output_path}")
        print()

    try:
        # Parse ZPL file
        if args.verbose:
            print("Parsing ZPL file...")

        zpl_parser = ZPLParser()
        labels = zpl_parser.parse_file(str(input_path))

        if args.verbose:
            print(f"✓ Found {len(labels)} unique products")
            print(f"✓ Generating {len(labels)} labels (one per product)")
            print(f"  Note: Quantity field indicates items in box, not label copies")
            print()

            # Show first few labels
            print("Sample labels:")
            for i, label in enumerate(labels[:3], 1):
                print(f"  {i}. {label.product_name[:50]}...")
                print(f"     SKU: {label.sku}, Qty: {label.quantity} items in box")
            if len(labels) > 3:
                print(f"  ... and {len(labels) - 3} more")
            print()

        # Generate PDF
        if args.verbose:
            print("Generating PDF...")

        pdf_gen = PDFGenerator()
        pdf_gen.generate_pdf(labels, str(output_path))

        if args.verbose:
            print(f"✓ PDF generated successfully")
            print()

        print(f"✓ PDF generated: {output_path}")

        sys.exit(0)

    except ZPLParseError as e:
        print(f"Error parsing ZPL file: {e}", file=sys.stderr)
        sys.exit(1)

    except PDFGenerationError as e:
        print(f"Error generating PDF: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
