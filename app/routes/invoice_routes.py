import os
import tempfile
import shutil
import httpx
from fastapi import APIRouter, HTTPException, BackgroundTasks
from starlette.responses import StreamingResponse
from docxtpl import DocxTemplate
from app.models.pydantic_models.generate_invoice_file.generate_invoice_schema import GenerateInvoiceFile
from app.services.invoice_template_service import PrintInvoiceService

router = APIRouter(tags=["Generate Invoice"])


@router.post("/generate-invoice-file")
async def generate_invoice(
    invoice_data: GenerateInvoiceFile,
    background_tasks: BackgroundTasks,
):
    """
    Generate a PDF invoice using a remote DOCX template URL and data context.
    """
    try:
        tmpdir = tempfile.mkdtemp()
        template_path = os.path.join(tmpdir, "template.docx")
        rendered_path = os.path.join(tmpdir, "output.docx")

        # ===========================
        # 1. Download DOCX template
        # ===========================
        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            response = await client.get(str(invoice_data.file_url))
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to download DOCX template.")
            with open(template_path, "wb") as f:
                f.write(response.content)

        # ===========================
        # 2. Render DOCX with context
        # ===========================
        doc = DocxTemplate(template_path)
        doc.render(invoice_data.invoice_dict)
        doc.save(rendered_path)

        # ===========================
        # 3. Convert to PDF
        # ===========================
        pdf_path = await PrintInvoiceService.generate_invoice_pdf(
            rendered_path, invoice_data.invoice_dict
        )

        # Cleanup after response
        background_tasks.add_task(shutil.rmtree, tmpdir, ignore_errors=True)

        filename_no_ext = os.path.splitext(os.path.basename(rendered_path))[0]
        return StreamingResponse(
            open(pdf_path, "rb"),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename_no_ext}.pdf"'
            },
            background=background_tasks,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
