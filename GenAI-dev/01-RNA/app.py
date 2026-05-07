from flask import Flask, request, jsonify
import numpy as np
import joblib
from tensorflow import keras

app = Flask(__name__)
model  = keras.models.load_model("housing_model.keras")
scaler = joblib.load("scaler.pkl")

FEATURES = ["area", "bedrooms", "bathrooms", "stories", "mainroad",
            "guestroom", "basement", "hotwaterheating", "airconditioning",
            "parking", "prefarea", "furnishingstatus"]

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    X = np.array([[data[f] for f in FEATURES]])
    X_sc = scaler.transform(X)
    price = model.predict(X_sc, verbose=0).flatten()[0]
    return jsonify({"predicted_price": round(float(price), 2)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)