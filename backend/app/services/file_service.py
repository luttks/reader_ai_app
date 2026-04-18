import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, File
from app.parsers.parser_factory import ParserFactory
from app.core.config import settings

def ensure_upload_dir() -> None:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

def get_file_extension(filename: UploadFile) -> str:
    return Path(filename).suffix.lower()

def validate_extension(filename: str) -> str:
    file_ext = get_file_extension(filename)
    allowed = [ext.strip().lower() for ext in settings.ALLOWED_EXTENSIONS.split(",")]

    if file_ext not in allowed:
        raise HTTPException(status_code=400, 
                detail=f"Unsupported file type: {file_ext}. Allowed types are: {', '.join(allowed)}."
                )

    return file_ext

def save_upload_file(file: UploadFile) -> tuple[str, str]:
    ensure_upload_dir()
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is missing")
    
    file_ext = validate_extension(file.filename)
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    save_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    with open(save_path, "wb") as out_file:
        content = file.file.read()
        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if len(content) > max_size:
            raise HTTPException(status_code=413, detail=f"File size exceeds limit of {settings.MAX_UPLOAD_SIZE_MB}MB")

        out_file.write(content)

    return save_path, file_ext

def parse_file(file_path: str, file_ext: str) -> str:
    parser = ParserFactory.get_parser(file_ext)
    return parser.parse(file_path)