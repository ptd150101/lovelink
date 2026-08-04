from io import BytesIO
from PIL import Image
import pytest
from apps.profiles.image_processing import _open_image, InvalidImage

def test_open_image_normalizes_rgb_and_strips_metadata():
    image = Image.new("RGBA", (200, 300), (255, 0, 0, 128))
    data = BytesIO(); image.save(data, "PNG")
    result = _open_image(data.getvalue())
    assert result.mode == "RGB"
    assert result.size == (200, 300)

def test_open_image_rejects_non_image():
    with pytest.raises(InvalidImage):
        _open_image(b"not-an-image")
