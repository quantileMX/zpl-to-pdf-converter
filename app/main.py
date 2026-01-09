"""
ZPL to PDF Converter - FastAPI Web Application

RESTful API for converting Zebra ZPL label files to PDF documents.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from typing import List
import tempfile
import os
import zipfile
from pathlib import Path

from app.parser.zpl_parser import ZPLParser, ZPLParseError
from app.generator.pdf_generator import PDFGenerator, PDFGenerationError
from app.models.label import ConversionResult


# Create FastAPI app
app = FastAPI(
    title="ZPL to PDF Converter",
    description="Convert Zebra ZPL label files to printable PDF documents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = ['.txt']


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "ZPL to PDF Converter API",
        "version": "1.0.0",
        "description": "Convert Zebra ZPL label files to PDF",
        "endpoints": {
            "convert_single": "POST /convert",
            "convert_bulk": "POST /convert-bulk",
            "health_check": "GET /health",
            "documentation": "GET /docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "zpl-to-pdf-converter"
    }


@app.post("/convert", response_class=FileResponse)
async def convert_single_file(file: UploadFile = File(...)):
    """
    Convert a single ZPL file to PDF

    Args:
        file: Uploaded ZPL text file

    Returns:
        PDF file download

    Raises:
        HTTPException: If conversion fails
    """
    # Validate file
    await _validate_upload(file)

    # Save uploaded file to temp location
    tmp_input = None
    tmp_output = None

    try:
        # Create temp input file
        tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
        content = await file.read()

        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large (max {MAX_FILE_SIZE / 1024 / 1024}MB)"
            )

        tmp_input.write(content)
        tmp_input.close()

        # Parse ZPL
        parser = ZPLParser()
        labels = parser.parse_file(tmp_input.name)

        if not labels:
            raise HTTPException(
                status_code=400,
                detail="No valid labels found in file"
            )

        # Generate PDF
        tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        tmp_output.close()

        generator = PDFGenerator()
        generator.generate_pdf(labels, tmp_output.name)

        # Return PDF file
        output_filename = Path(file.filename).stem + ".pdf"

        return FileResponse(
            tmp_output.name,
            media_type="application/pdf",
            filename=output_filename,
            headers={
                "Content-Disposition": f"attachment; filename={output_filename}"
            }
        )

    except ZPLParseError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ZPL format: {str(e)}"
        )

    except PDFGenerationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"PDF generation failed: {str(e)}"
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )

    finally:
        # Clean up input file
        if tmp_input and os.path.exists(tmp_input.name):
            try:
                os.unlink(tmp_input.name)
            except:
                pass


@app.post("/convert-bulk")
async def convert_bulk_files(files: List[UploadFile] = File(...)):
    """
    Convert multiple ZPL files and return as ZIP

    Args:
        files: List of uploaded ZPL files

    Returns:
        ZIP file containing all PDFs

    Raises:
        HTTPException: If conversion fails
    """
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files provided"
        )

    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 files per request"
        )

    results = []
    temp_files = []
    pdf_paths = []

    try:
        # Process each file
        for uploaded_file in files:
            # Validate file
            await _validate_upload(uploaded_file)

            # Create temp input file
            tmp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
            content = await uploaded_file.read()

            if len(content) > MAX_FILE_SIZE:
                results.append({
                    "filename": uploaded_file.filename,
                    "success": False,
                    "error": "File too large"
                })
                os.unlink(tmp_input.name)
                continue

            tmp_input.write(content)
            tmp_input.close()
            temp_files.append(tmp_input.name)

            try:
                # Parse and convert
                parser = ZPLParser()
                labels = parser.parse_file(tmp_input.name)

                # Generate PDF
                output_filename = Path(uploaded_file.filename).stem + ".pdf"
                tmp_output = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix='.pdf',
                    prefix=Path(uploaded_file.filename).stem + "_"
                )
                tmp_output.close()
                temp_files.append(tmp_output.name)

                generator = PDFGenerator()
                generator.generate_pdf(labels, tmp_output.name)

                pdf_paths.append((output_filename, tmp_output.name))

                results.append({
                    "filename": uploaded_file.filename,
                    "success": True,
                    "labels": len(labels),
                    "copies": sum(l.quantity for l in labels)
                })

            except Exception as e:
                results.append({
                    "filename": uploaded_file.filename,
                    "success": False,
                    "error": str(e)
                })

        # Create ZIP file
        if not pdf_paths:
            raise HTTPException(
                status_code=400,
                detail="No files could be converted"
            )

        zip_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        zip_file.close()
        temp_files.append(zip_file.name)

        with zipfile.ZipFile(zip_file.name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for pdf_filename, pdf_path in pdf_paths:
                zf.write(pdf_path, pdf_filename)

        return FileResponse(
            zip_file.name,
            media_type="application/zip",
            filename="converted_labels.zip",
            headers={
                "Content-Disposition": "attachment; filename=converted_labels.zip"
            }
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Bulk conversion failed: {str(e)}"
        )

    finally:
        # Clean up temp files (keep ZIP for response)
        for temp_file in temp_files:
            if temp_file != zip_file.name and os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass


async def _validate_upload(file: UploadFile) -> None:
    """
    Validate uploaded file

    Args:
        file: Uploaded file

    Raises:
        HTTPException: If validation fails
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No filename provided"
        )

    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )


# Exception handlers
@app.exception_handler(ZPLParseError)
async def zpl_parse_error_handler(request, exc):
    """Handle ZPL parsing errors"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid ZPL format",
            "detail": str(exc)
        }
    )


@app.exception_handler(PDFGenerationError)
async def pdf_generation_error_handler(request, exc):
    """Handle PDF generation errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "PDF generation failed",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
