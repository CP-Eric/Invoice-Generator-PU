import asyncio
import logging
import os
import platform
import shutil
import tempfile

from docxtpl import DocxTemplate
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class PrintInvoiceService:
    @staticmethod
    def _find_soffice() -> str:
        """
        Locate LibreOffice binary (cross-platform).
        """
        env_path = os.environ.get("LIBREOFFICE_PATH")
        if env_path and os.path.isfile(env_path):
            return env_path

        which_path = shutil.which("soffice")
        if which_path:
            return which_path

        system = platform.system()
        candidates = []

        if system == "Windows":
            candidates = [
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            ]
        elif system == "Linux":
            candidates = [
                "/usr/bin/soffice",
                "/usr/local/bin/soffice",
                "/snap/bin/libreoffice",
                "/usr/lib/libreoffice/program/soffice",
            ]
        elif system == "Darwin":
            candidates = [
                "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            ]

        for p in candidates:
            if os.path.isfile(p):
                return p

        raise HTTPException(
            status_code=500,
            detail="LibreOffice 'soffice' binary not found. Install LibreOffice or set LIBREOFFICE_PATH."
        )

    @staticmethod
    async def _convert_docx_to_pdf(input_docx: str, out_dir: str, timeout_sec: int = 120) -> str:
        """
        Convert DOCX → PDF with LibreOffice (async).
        """
        soffice = PrintInvoiceService._find_soffice()
        cmd = [
            soffice,
            "--headless",
            "--norestore",
            "--nolockcheck",
            "--nodefault",
            "--convert-to", "pdf:writer_pdf_Export",
            "--outdir", out_dir,
            input_docx,
        ]

        logger.info(f"Running LibreOffice: {' '.join(cmd)}")

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
            except asyncio.TimeoutError:
                proc.kill()
                raise HTTPException(status_code=500, detail="LibreOffice conversion timed out.")

            if proc.returncode != 0:
                err = (stderr or stdout or b"").decode(errors="ignore")
                logger.error(f"LibreOffice failed: {err}")
                raise HTTPException(status_code=500, detail=f"LibreOffice failed: {err}")

            base = os.path.splitext(os.path.basename(input_docx))[0]
            pdf_path = os.path.join(out_dir, f"{base}.pdf")

            if not os.path.exists(pdf_path):
                raise HTTPException(status_code=500, detail="PDF not created by LibreOffice.")

            return pdf_path

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Unexpected error during DOCX→PDF conversion")
            raise HTTPException(status_code=500, detail=f"Conversion error: {e}")

    @staticmethod
    def _safe_remove(path: str):
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception as e:
            logger.warning(f"Failed to remove temp file: {path}, Error: {e}", exc_info=True)

    @staticmethod
    async def generate_invoice_pdf(template_path: str, context: dict) -> str:
        """
        Fill DOCX template with context, convert to PDF, return PDF path.
        """
        tmp_filled_docx = None
        tmp_dir = tempfile.mkdtemp()

        try:
            # 1. Fill DOCX
            doc = DocxTemplate(template_path)

            # Apply aliasing
            doc.render(context)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_out:
                tmp_filled_docx = tmp_out.name
            doc.save(tmp_filled_docx)

            # 2. Convert to PDF
            pdf_path = await PrintInvoiceService._convert_docx_to_pdf(tmp_filled_docx, tmp_dir)
            return pdf_path

        except Exception as e:
            raise e
        finally:
            # Clean up DOCX
            if tmp_filled_docx:
                PrintInvoiceService._safe_remove(tmp_filled_docx)
