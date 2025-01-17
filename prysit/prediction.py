import os
import keras
import numpy as np
import tensorflow as tf

from prysit import model as model_lib
from prysit import io_local
from prysit import constants
from prysit import sanitize


def predict(data, d_model):
    # check for mandatory keys
    x = io_local.get_array(data, d_model["config"]["x"])

    tf.compat.v1.keras.backend.set_session(d_model["session"])
    with d_model["graph"].as_default():
        prediction = d_model["model"].predict(
            x, verbose=True, batch_size=constants.PRED_BATCH_SIZE
        )

    if d_model["config"]["prediction_type"] == "intensity":
        data["intensities_pred"] = prediction
        data = sanitize.prediction(data)
    elif d_model["config"]["prediction_type"] == "iRT":
        scal = float(d_model["config"]["iRT_rescaling_var"])
        mean = float(d_model["config"]["iRT_rescaling_mean"])
        data["iRT"] = prediction * np.sqrt(scal) + mean
    else:
        raise ValueError("model_config misses parameter")
    return data
