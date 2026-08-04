from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from common.storage.s3 import delete_object, get_object_bytes, put_object_bytes

MAX_PIXELS = 40_000_000
PROFILE_SIZE = (1200, 1500)
PROFILE_THUMBNAIL_SIZE = (480, 600)


class InvalidImage(ValueError):
    pass


def _open_image(data: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(data))
        image.verify()
        image = Image.open(BytesIO(data))
        image = ImageOps.exif_transpose(image)
        if image.width * image.height > MAX_PIXELS:
            raise InvalidImage("Ảnh có độ phân giải quá lớn.")
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")
        elif image.mode == "RGBA":
            background = Image.new("RGB", image.size, "white")
            background.paste(image, mask=image.getchannel("A"))
            image = background
        return image
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InvalidImage("Nội dung file không phải ảnh hợp lệ.") from exc


def normalize_profile_image(bucket: str, temporary_key: str) -> dict:
    data, _ = get_object_bytes(bucket, temporary_key)
    image = _open_image(data)
    image = ImageOps.fit(
        image,
        PROFILE_SIZE,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    base = temporary_key.rsplit(".", 1)[0]
    object_key = f"{base}.webp"
    thumbnail_key = f"{base}-thumb.webp"

    full = BytesIO()
    image.save(full, "WEBP", quality=88, method=6)
    thumbnail = image.copy()
    thumbnail.thumbnail(PROFILE_THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
    thumb = BytesIO()
    thumbnail.save(thumb, "WEBP", quality=82, method=6)

    put_object_bytes(
        bucket, object_key, full.getvalue(), "image/webp", public=True
    )
    put_object_bytes(
        bucket, thumbnail_key, thumb.getvalue(), "image/webp", public=True
    )
    if temporary_key not in {object_key, thumbnail_key}:
        delete_object(bucket, temporary_key)
    return {
        "object_key": object_key,
        "thumbnail_object_key": thumbnail_key,
        "width": image.width,
        "height": image.height,
        "mime_type": "image/webp",
        "file_size": len(full.getvalue()),
    }


def normalize_private_image(bucket: str, temporary_key: str) -> dict:
    data, _ = get_object_bytes(bucket, temporary_key)
    image = _open_image(data)
    image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
    object_key = f"{temporary_key.rsplit('.', 1)[0]}.webp"
    output = BytesIO()
    image.save(output, "WEBP", quality=90, method=6)
    put_object_bytes(
        bucket, object_key, output.getvalue(), "image/webp", public=False
    )
    if object_key != temporary_key:
        delete_object(bucket, temporary_key)
    return {
        "object_key": object_key,
        "mime_type": "image/webp",
        "file_size": len(output.getvalue()),
    }
