import numpy as np
import pandas as pd
from pyteomics.mzml import MzML
from pathlib import Path
from prysit.predictor import Predictor


def get_observed_intensities(predicted_mzs, observed_mzs, observed_intensities):
    intensities = np.max(np.multiply((np.abs((predicted_mzs[:, np.newaxis] - observed_mzs)/observed_mzs * 1e6) < 10),
                                     observed_intensities), axis=1)
    return intensities


def normalized_spectral_contrast_angle(v1, v2):
    v1 = np.sqrt(v1)/np.sqrt(np.sum(np.abs(v1)))
    v2 = np.sqrt(v2) / np.sqrt(np.sum(np.abs(v2)))
    return 1 - 2 * np.arccos(min(np.dot(v1, v2), 1.0)) / np.pi


class Comparer:
    def __init__(self, mzml_file: str, fragmentation_model: str = 'non-tryptic-hcd'):
        if not Path(mzml_file).exists() and Path(mzml_file).is_file():
            raise FileNotFoundError(f'{mzml_file} does not exist.')
        self.mzml = MzML(mzml_file)
        self.predictor = Predictor(fragmentation_model)

    def score_msms_prediction(self, scan_number: int, predicted_spectrum: pd.DataFrame):
        """
        Compares Prosit predicted fragments against observed. This takes the "msms" output format.
        :param scan_number:
        :param predicted_spectrum:
        :return:
        """
        obs_mz = self.mzml[scan_number-1]['m/z array']
        obs_int = self.mzml[scan_number-1]['intensity array']
        pred_mz = np.array(predicted_spectrum['Masses'][0].split(';'), dtype=float)
        pred_int = np.array(predicted_spectrum['Intensities'][0].split(';'), dtype=float)

        matched_obs_int = get_observed_intensities(pred_mz, obs_mz, obs_int)

        return normalized_spectral_contrast_angle(matched_obs_int, pred_int)

    def score_generic_prediction(self, scan_number: int, predicted_spectrum: pd.DataFrame):
        """
        Compares Prosit predicted fragments against observed. This takes the "generic" output format. Because
        this format includes all predicted peptides, it is possible to compare multiple predictions against a single
        observed spectrum at the same time, e.g. chimeric spectra.
        :param scan_number:
        :param predicted_spectrum:
        :return:
        """
        obs_mz = self.mzml[scan_number-1]['m/z array']
        obs_int = self.mzml[scan_number-1]['intensity array']
        pred_mz = predicted_spectrum['FragmentMz'].to_numpy()
        pred_int = predicted_spectrum['RelativeIntensity'].to_numpy()

        matched_obs_int = get_observed_intensities(pred_mz, obs_mz, obs_int)

        return normalized_spectral_contrast_angle(matched_obs_int, pred_int)

    def score_peptide_sequence(self, scan_number: int,
                               peptide_sequence: str,
                               collision_energy: float,
                               charge: int):

        predicted_spectrum = self.predictor.predict_peptides(peptide_sequence, collision_energy, charge)
        score = self.score_generic_prediction(scan_number, predicted_spectrum)

        return score
