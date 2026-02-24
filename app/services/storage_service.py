import os


def ensure_upload_dirs(upload_dir: str, resolutions: dict) -> None:
    for label in resolutions.keys():
        os.makedirs(f"{upload_dir}/{label}", exist_ok=True)


def delete_image_files(upload_dir: str, resolutions: dict, file_id: str) -> None:
    for label in resolutions.keys():
        file_path = f"{upload_dir}/{label}/{file_id}"
        if os.path.exists(file_path):
            os.remove(file_path)
