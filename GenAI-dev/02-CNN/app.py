import json
import base64
import numpy as np
from io import BytesIO
from PIL import Image

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tensorflow as tf
from tensorflow.keras.layers import MaxPooling2D

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = tf.keras.models.load_model("model/quickdraw_cnn.keras")

with open("model/class_map.json") as f:
    class_map = json.load(f)

# Warmup: construye el grafo antes de crear el modelo intermedio
model.predict(np.zeros((1, 28, 28, 1), dtype="float32"), verbose=0)

# Modelo intermedio: salidas tras cada MaxPooling (bloque 1 y bloque 2)
pool_layers = [l for l in model.layers if isinstance(l, MaxPooling2D)]
activation_model = tf.keras.Model(
    inputs=model.inputs,
    outputs=[pool_layers[0].output, pool_layers[1].output]
)


def preprocess(image_b64: str) -> np.ndarray:
    img_data = base64.b64decode(image_b64.split(",")[-1])
    img = Image.open(BytesIO(img_data)).convert("L")

    # Invertir para trabajar con trazo blanco sobre negro
    arr = np.array(img, dtype="float32")
    arr = 255.0 - arr

    # Recortar al bounding box del dibujo con un margen del 10%
    rows = np.any(arr > 10, axis=1)
    cols = np.any(arr > 10, axis=0)
    if rows.any() and cols.any():
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        h, w = rmax - rmin, cmax - cmin
        pad = max(int(max(h, w) * 0.1), 2)
        rmin = max(rmin - pad, 0)
        rmax = min(rmax + pad, arr.shape[0])
        cmin = max(cmin - pad, 0)
        cmax = min(cmax + pad, arr.shape[1])
        arr = arr[rmin:rmax, cmin:cmax]

    # Centrar en un cuadrado y redimensionar a 28x28
    h, w = arr.shape
    size = max(h, w)
    square = np.zeros((size, size), dtype="float32")
    y_off = (size - h) // 2
    x_off = (size - w) // 2
    square[y_off:y_off + h, x_off:x_off + w] = arr

    resized = np.array(Image.fromarray(square).resize((28, 28)))
    return (resized / 255.0).reshape(1, 28, 28, 1)


def feature_map_to_b64(fmap: np.ndarray) -> str:
    mn, mx = fmap.min(), fmap.max()
    norm = ((fmap - mn) / (mx - mn) * 255).astype(np.uint8) if mx > mn else np.zeros_like(fmap, dtype=np.uint8)
    img = Image.fromarray(norm, mode="L")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


class ImagePayload(BaseModel):
    image: str


@app.post("/predict")
def predict(payload: ImagePayload):
    arr = preprocess(payload.image)
    probs = model.predict(arr, verbose=0)[0]
    idx = int(np.argmax(probs))
    return {
        "category"  : class_map[str(idx)],
        "confidence": float(round(probs[idx], 4)),
        "all_probs" : {class_map[str(i)]: float(round(p, 4)) for i, p in enumerate(probs)},
    }


@app.post("/activations")
def activations(payload: ImagePayload):
    arr = preprocess(payload.image)
    act1, act2 = activation_model.predict(arr, verbose=0)
    n1 = min(16, act1.shape[-1])
    n2 = min(16, act2.shape[-1])
    return {
        "block1": [feature_map_to_b64(act1[0, :, :, i]) for i in range(n1)],
        "block2": [feature_map_to_b64(act2[0, :, :, i]) for i in range(n2)],
    }
