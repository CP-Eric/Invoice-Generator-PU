from pydantic import BaseModel, HttpUrl, Field


class GenerateInvoiceFile(BaseModel):
    """
    Schema for generating a PDF invoice from a DOCX template.
    """

    file_url: HttpUrl = Field(
        ...,
        description="Public or signed URL of the DOCX invoice template.",
        example="https://example.com/invoice_template.docx"
    )

    invoice_dict: dict = Field(
        ...,
        description="Key-value data used to fill placeholders inside the DOCX template.",
        example={
            "invoice_number": "INV-2025-001",
            "date": "2025-11-06",
            "client_name": "John Doe",
            "address": "123 Main Street, New York, NY",
            "items": [
                {"description": "Website Development", "price": "1200.00"},
                {"description": "Hosting (1 year)", "price": "300.00"}
            ],
            "subtotal": "1500.00",
            "tax": "0.00",
            "total": "1500.00",
            "notes": "Thank you for your business."
        }
    )
