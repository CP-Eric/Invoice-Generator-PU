from pydantic import BaseModel


class UploadFile(BaseModel):
    message: str
    file_id: str
    uq_filename: str


class Files(BaseModel):
    file_name: str
    file_id: str
    size_bytes: int
    upload_timestamp: int


class ListFiles(BaseModel):
    files: list[Files]


class DeleteFile(BaseModel):
    message: str
    file_id: str
    filename: str
