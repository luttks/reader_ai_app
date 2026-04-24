import os
import traceback

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.document import DocumentResponse, DocumentCreate
from app.services.file_service import save_upload_file, parse_file
from app.services.document_service import create_document

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("", response_model=DocumentResponse)
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Invalid file")

    try:
        print(f"[UPLOAD] file: {file.filename}")

        save_path, file_ext = save_upload_file(file)
        print(f"[UPLOAD] save_path: {save_path}, file_ext: {file_ext}")

        file_type = file_ext.replace(".", "").lower()

        layout = None

        if file_type == "pdf":
            from app.services.layout_service import inspect_pdf_layout
            layout = inspect_pdf_layout(save_path)
            raw_text = layout.get("raw_text", "")
        else:
            raw_text = parse_file(save_path, file_ext)

        payload = DocumentCreate(
            title=os.path.splitext(file.filename)[0],
            file_name=file.filename,
            file_type=file_type,
            file_path=save_path,
            raw_text=raw_text,
        )

        document = create_document(db, payload, layout_json=layout)
        return document

    except HTTPException:
        raise
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    except Exception as e:
        print("[UPLOAD ERROR]")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload and parse file: {str(e)}"
        ) from e
