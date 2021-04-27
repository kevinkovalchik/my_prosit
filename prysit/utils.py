'''
This file modified by Kevin Kovalchik
'''

from prysit.constants import MAX_ION, ION_TYPES, ALPHABET_S, MODEL_DIR
from pathlib import Path
from typing import Sequence


def check_mandatory_keys(dictionary, keys):
    for key in keys:
        if key not in dictionary.keys():
            raise KeyError("key {} is missing".format(key))
    return True


def reshape_dims(array, nlosses=1, z=3):
    return array.reshape([array.shape[0], MAX_ION, len(ION_TYPES), nlosses, z])


def get_sequence(sequence):
    d = ALPHABET_S
    return "".join([d[i] if i in d else "" for i in sequence])


def sequence_integer_to_str(array):
    sequences = [get_sequence(array[i]) for i in range(array.shape[0])]
    return sequences


def peptide_parser(p):
    p = p.replace("_", "")
    if p[0] == "(":
        raise ValueError("sequence starts with '('")
    n = len(p)
    i = 0
    while i < n:
        if i < n - 3 and p[i + 1] == "(":
            j = p[i + 2 :].index(")")
            offset = i + j + 3
            yield p[i:offset]
            i = offset
        else:
            yield p[i]
            i += 1


def download_models(models: Sequence[str] = ('tryptic', 'non-tryptic', 'irt'), directory=MODEL_DIR) -> None:
    """
    Download Tensorflow models required by Prosit.
    :param models: Sequence containing the models to download. Can contain 'tryptic', 'non-tryptic', and/or 'irt'.
    :param directory: Directory in which to save the models. Defaults to ~/.my-prosit_models
    :return: None
    """
    import requests
    from zipfile import ZipFile
    from io import BytesIO
    urls = {'non-tryptic': 'https://ndownloader.figshare.com/files/24635243',
            'tryptic': 'https://ndownloader.figshare.com/files/13687205',
            'irt': 'https://ndownloader.figshare.com/files/13698893'}

    if isinstance(models, str):
        models = [models]

    for model in models:
        print(f'Downloading {model} model')
        response = requests.get(urls[model], verify=True)
        print(f'Extracting {model} model')
        with ZipFile(BytesIO(response.content)) as zfile:
            if not Path(directory, model).exists():
                Path(directory, model).mkdir(parents=True)
            zfile.extractall(Path(directory, model))
