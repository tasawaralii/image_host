from datetime import datetime

from fastapi import APIRouter, File, Header, HTTPException, UploadFile

from ..config import API_KEY, DB_PATH, RESOLUTIONS, UPLOAD_DIR
from ..db import get_db
from ..services.images_service import build_urls, parse_file_sizes, save_image_variants, serialize_file_sizes
from ..services.storage_service import delete_image_files

router = APIRouter()


@router.post("/upload")
async def upload_image(file: UploadFile = File(...), x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    contents = await file.read()
    try:
        file_id, original_width, original_height, file_sizes = save_image_variants(
            contents,
            UPLOAD_DIR,
            RESOLUTIONS,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid image file")

    conn = get_db(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO images (id, original_filename, uploaded_at, original_width, original_height, file_sizes)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            file_id,
            file.filename,
            datetime.now().isoformat(),
            original_width,
            original_height,
            serialize_file_sizes(file_sizes),
        ),
    )
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "file_id": file_id,
        "original_filename": file.filename,
        "dimensions": {"width": original_width, "height": original_height},
        "file_sizes": file_sizes,
        "urls": build_urls(file_id, RESOLUTIONS),
    }


@router.get("/list")
async def list_images(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    conn = get_db(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM images ORDER BY uploaded_at DESC")
    rows = c.fetchall()
    conn.close()

    images = []
    for row in rows:
        file_id = row["id"]
        file_sizes = parse_file_sizes(row["file_sizes"])
        images.append(
            {
                "file_id": file_id,
                "original_filename": row["original_filename"],
                "uploaded_at": row["uploaded_at"],
                "dimensions": {"width": row["original_width"], "height": row["original_height"]},
                "file_sizes": file_sizes,
                "urls": build_urls(file_id, RESOLUTIONS),
            }
        )

    return {"total": len(images), "images": images}


@router.get("/images/{file_id}")
async def get_image(file_id: str, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    conn = get_db(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM images WHERE id = ?", (file_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Image not found")

    file_sizes = parse_file_sizes(row["file_sizes"])
    return {
        "file_id": row["id"],
        "original_filename": row["original_filename"],
        "uploaded_at": row["uploaded_at"],
        "dimensions": {"width": row["original_width"], "height": row["original_height"]},
        "file_sizes": file_sizes,
        "urls": build_urls(file_id, RESOLUTIONS),
    }


@router.delete("/images/{file_id}")
async def delete_image(file_id: str, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    conn = get_db(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM images WHERE id = ?", (file_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Image not found")

    delete_image_files(UPLOAD_DIR, RESOLUTIONS, file_id)

    c.execute("DELETE FROM images WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()

    return {"status": "deleted", "file_id": file_id}
