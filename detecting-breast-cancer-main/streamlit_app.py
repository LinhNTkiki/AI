from pathlib import Path

import numpy as np
import streamlit as st
import tensorflow as tf
from PIL import Image
from streamlit.runtime.uploaded_file_manager import UploadedFile

IMG_SIZE = 224
SAMPLE_IMG_DIR = Path("sample_images")

title = "Dự đoán ung thư vú"
st.set_page_config(page_title=title)
st.header(title)
st.markdown(
    "Dự đoán khối u vú trên hình ảnh siêu âm [ungthuvu][hp] là"
    " *benign*, *normal* or *malignant (ung thư)*.\n\n"
    "[hp]: https://vi.wikipedia.org/wiki/Ung_th%C6%B0_v%C3%BA"
)


def load_image(
    image: Path | UploadedFile, resize: bool = False
) -> Image.Image | tf.Tensor:
    """Convert an input image into the form expected by the model.

    Args:
        image (Path | UploadedFile): Image input.
        resize (bool): Whether or not to resize the image.

    Returns:
        PIL.image.Image | tensorflow.Tensor: A PIL Image. Or a 3D tensor, if
        resize is True.
    """
    img = Image.open(image)
    if resize:
        img = img.convert("RGB")  # Ensure image is in RGB mode
        img = tf.image.resize_with_pad(img, IMG_SIZE, IMG_SIZE)
    return img


@st.cache_data
def get_sample_image_files() -> dict[str, list]:
    """Fetch processed sample images, grouped by label.

    Returns:
        dict: Keys are labels ("benign", "malignant", "normal"). Values are lists of
        images.
    """
    return {
        dir.name: [load_image(file) for file in dir.glob("*.jpg")]
        for dir in SAMPLE_IMG_DIR.iterdir()
    }


@st.cache_resource
def load_model() -> tf.keras.Model:
    """Fetch pretrained model.

    Returns:
        tf.keras.Model: Trained convolutional neural network.
    """
    model_path = "cnn_model_multiclass.h5"
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    return tf.keras.models.load_model(model_path)


def get_prediction(image: Image.Image | tf.Tensor) -> None:
    """Obtain a prediction for the supplied image, and format the results for
    display.

    Args:
        image (Image | Tensor): An image (PIL Image or 3D tensor).
    """
    pred = model.predict(np.expand_dims(image, 0), verbose=0)[0]
    class_names = ["benign", "malignant", "normal"]
    predicted_class = class_names[np.argmax(pred)]
    st.success(f"Prediction: {predicted_class}")
    st.markdown(f"Predicted probabilities: {dict(zip(class_names, pred))}")
  

sample_images = get_sample_image_files()

try:
    model = load_model()
except FileNotFoundError as e:
    st.error(f"Error: {e}")
    st.stop()

upload_tab, sample_tab = st.tabs(["Tải ảnh lên", "Sử dụng ảnh mẫu"])

with upload_tab:
    with st.form("image-input-form", clear_on_submit=True):
        file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("submit")
        if file:
            img = load_image(file, resize=True)
            st.image(img.numpy().astype("uint8"))
            get_prediction(img)


st.caption(
    "Phân tích dữ liệu thăm dò và đào tạo mô hình đã được thực hiện trong "
    "[this Kaggle notebook][nb].\n\n"
    "[nb]: https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset-with-computer-vision"
)
