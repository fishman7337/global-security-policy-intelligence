from __future__ import annotations

import numpy as np


def build_tabular_mlp(input_dim: int, output_classes: int):
    """Return a small Keras MLP when TensorFlow is installed."""
    try:
        from tensorflow import keras
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError("TensorFlow is required for the deep learning extension.") from exc

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(input_dim,)),
            keras.layers.Dense(128, activation="relu"),
            keras.layers.Dropout(0.25),
            keras.layers.Dense(64, activation="relu"),
            keras.layers.Dense(output_classes, activation="softmax"),
        ]
    )
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def window_series(values: np.ndarray, window: int = 12) -> tuple[np.ndarray, np.ndarray]:
    x, y = [], []
    for index in range(window, len(values)):
        x.append(values[index - window : index])
        y.append(values[index])
    return np.asarray(x), np.asarray(y)

