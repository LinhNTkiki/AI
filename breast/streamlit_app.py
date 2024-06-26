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

def load_image(image: Path | UploadedFile, resize: bool = False) -> tf.Tensor:
    """Convert an input image into the form expected by the model.

    Args:
        image (Path | UploadedFile): Image input.
        resize (bool): Whether or not to resize the image.

    Returns:
        tf.Tensor: A 3D tensor.
    """
    img = Image.open(image)
    img = img.convert("RGB")  # Ensure image is in RGB mode
    img = np.array(img)
    if resize:
        img = tf.image.resize_with_pad(img, IMG_SIZE, IMG_SIZE)
    img = tf.convert_to_tensor(img, dtype=tf.float32) / 255.0  # Normalize to [0, 1]
    return img

@st.cache_data
def get_sample_image_files() -> dict[str, list]:
    """Fetch processed sample images, grouped by label.

    Returns:
        dict: Keys are labels ("benign" / "malignant" / "normal"). Values are lists of
        images.
    """
    return {
        dir.name: [load_image(file, resize=True) for file in dir.glob("*.jpg")]
        for dir in SAMPLE_IMG_DIR.iterdir() if dir.is_dir()
    }

@st.cache_resource
def load_model() -> tf.keras.Model:
    """Fetch pretrained model.

    Returns:
        tf.keras.Model: Trained convolutional neural network.
    """
    return tf.keras.models.load_model("cnn_model.h5")

def get_prediction(image: tf.Tensor) -> None:
    """Obtain a prediction for the supplied image, and format the results for display.

    Args:
        image (tf.Tensor): A 3D tensor.
    """
    pred = model.predict(np.expand_dims(image, 0), verbose=0)[0]
    pred_value = pred[0]  # Ensure pred is a scalar value

    if pred_value < 0.3:
        st.info(f"Result: {pred_value:.5f}")
        st.markdown("Inference at *threshold==0.3*: :blue['normal']")
    elif 0.3 <= pred_value <= 0.6:
        st.success(f"Result: {pred_value:.5f}")
        st.markdown("Inference at *threshold==0.5*: :green['benign']")
    else:
        st.warning(f"Result: {pred_value:.5f}")
        st.markdown("Inference at *threshold==0.6*: :orange['malignant']")
    st.caption(
        "The model's output node has *sigmoid activation*, with 'malignant' "
        "being the positive class (1), and 'benign' being the negative "
        "class (0). Values close to 1 suggest high chances of malignancy, "
        "and vice versa."
    )

sample_images = get_sample_image_files()
model = load_model()

upload_tab, sample_tab = st.tabs(["Tải ảnh lên", "Sử dụng ảnh mẫu"])

with upload_tab:
    with st.form("image-input-form", clear_on_submit=True):
        file = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("submit")
        if file and submitted:
            img = load_image(file, resize=True)
            st.image(img.numpy())
            get_prediction(img)

with sample_tab:
    if st.button("Get sample image", type="primary"):
        # Randomly select a sample image
        label = np.random.choice(list(sample_images.keys()))
        image_list = sample_images[label]
        idx = np.random.choice(len(image_list))
        img = image_list[idx]
        st.image(img.numpy(), caption=f"{label} sample")
        get_prediction(img)

st.caption(
    "Phân tích dữ liệu thăm dò và đào tạo mô hình đã được thực hiện trong "
    "[this Kaggle notebook][nb].\n\n"
    "[nb]: https://www.kaggle.com/datasets/aryashah2k/breast-ultrasound-images-dataset-with-computer-vision"
)