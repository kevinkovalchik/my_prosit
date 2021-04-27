import pandas as pd

import tensorflow as tf
import warnings
from prysit import constants, model, tensorize, prediction, converters
from typing import Union, List, Dict
from pathlib import Path
from numpy import ndarray
import tempfile


class Predictor:
    """
    A programmatic interface to the Prosit prediction tools.
    """
    def __init__(self, fragmentation_model: str = 'tryptic'):
        assert fragmentation_model in ['tryptic', 'non-tryptic-cid', 'non-tryptic-hcd']
        if not tf.test.is_gpu_available():
            tf.device('/cpu:0')
        if fragmentation_model == 'non-tryptic-cid':
            model_dir = constants.MODEL_NONTRYPTIC_CID_SPECTRA_DIR
        elif fragmentation_model == 'non-tryptic-hcd':
            model_dir = constants.MODEL_NONTRYPTIC_HCD_SPECTRA_DIR
        else:
            model_dir = constants.MODEL_TRYPTIC_SPECTRA_DIR
        warnings.filterwarnings("ignore")
        global d_spectra
        global d_irt
        self.d_spectra = {}
        self.d_irt = {}

        self.d_spectra["graph"] = tf.Graph()
        with self.d_spectra["graph"].as_default():
            self.d_spectra["session"] = tf.compat.v1.Session()
            with self.d_spectra["session"].as_default():
                self.d_spectra["model"], self.d_spectra["config"] = model.load(
                    model_dir=model_dir,
                    trained=True
                )
                self.d_spectra["model"].compile(optimizer="adam", loss="mse")
        self.d_irt["graph"] = tf.Graph()
        with self.d_irt["graph"].as_default():
            self.d_irt["session"] = tf.compat.v1.Session()
            with self.d_irt["session"].as_default():
                self.d_irt["model"], self.d_irt["config"] = model.load(constants.MODEL_IRT_DIR,
                                                                       trained=True)
                self.d_irt["model"].compile(optimizer="adam", loss="mse")

    def predict_csv(self,
                    filename: Union[str, Path],
                    output_format: str = 'generic') -> Union[pd.DataFrame, dict]:
        """
        Predict MS/MS fragmentation intensities and iRT from csv file.
        :param filename: The CSV file to read.
        :param output_format: Format for the output. Should be one of "generic", "msms" or "raw".
        :return: Predicted fragment intensisities and iRT values.
        """

        assert output_format in ['generic', 'msms', 'raw']
        df = pd.read_csv(filename)
        data = tensorize.csv(df)
        return self._predict(data, output_format)

    def predict_peptides(self,
                         modified_sequence: Union[List[str], str],
                         collision_energy: Union[List[float], float],
                         precursor_charge: Union[List[int], int],
                         output_format: str = 'generic') -> Union[pd.DataFrame, dict]:
        """
        Predict MS/MS fragmentation intensities and iRT for a single peptide.
        :param modified_sequence: Peptide sequence
        :param collision_energy: Collision energy to use for prediction
        :param precursor_charge: Precursor charge
        :param output_format: Format for the output. Should be one of "generic", "msms" or "raw".
        :return: Predicted fragment intensisities and iRT values.
        """
        data = tensorize.general_input(modified_sequence, collision_energy, precursor_charge)
        return self._predict(data, output_format)

    def _predict(self,
                 data: Dict[str, Union[float, ndarray, None]],
                 output_format: str = 'generic') -> Union[pd.DataFrame, dict]:
        """
        Predict MS/MS fragmentation intensities and iRT values from tensorized data. To be used with "predict_singe"
        and "predict_csv" functions.
        :param data: Tensorized peptide data
        :param output_format: Format for the output. Should be one of "generic", "msms" or "raw".
        :return: Predicted fragment intensisities and iRT values.
        """

        assert output_format in ['generic', 'msms', 'raw']

        data = prediction.predict(data, self.d_spectra)
        data = prediction.predict(data, self.d_irt)

        if output_format == 'generic':
            return converters.generic.convert_multiple_spectra(data)
        elif output_format == 'msms':
            return converters.maxquant.convert_prediction(data)
        else:
            return data
