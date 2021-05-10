I would like a version of Prosit I can use programmatically from within Python instead of 
using a Docker container. I can't use Docker on many HPCs. Perhaps I will accomplish this.

I have given it the silly name Prysit, which is sort of a combination of Python and Prosit. Doesn't really make 
that much sense because Prosit is already written in Python, but whatever...

Things to do:

1. The package is built on tensorflow v1. It is solid as-is (since it is designed to run in Docker), but for 
   use outside its intended Docker container this is difficult. v1 is not future-proof. v1 is not even very 
   easy to install anymore, especially not 1.10.1 which requires Python <= 3.6.
   - Migrate the package to TensorFlow v2. It uses Keras, so there might not be too much to do.
   The only hurdle I see is in the server.py `__main__` section, which uses `tf.Session`. I'm probably 
     missing other things too. Nothing is ever as easy as it seems it should be.
   - **ran tf_upgrade_v2 on the prosit directory. It only had to change a few things, so I was mostly 
     correct. Though, of course, I haven't actually been able to test anything yet.**
   - **changed a few things to use the `compat.v1` stuff**
   - **after the above changes, the server now runs outisde of Docker by invoking `python -m prysit.server`**
   - **made a version of the model.yml files which will work on CPU, so we no longer need GPUs to run it.**
      - *Note: This doesn't happen automatically, I'm just making a note here. Probably I will add a function that 
       makes a copy of the model yaml files and then modifies them appropriately, and then the correct model 
       will be chosen automatically or indicated by the user.*
2. Predictions seem to be made from within the server. At least, there are some variables that only get defined
in the the `__main__` section of server.py.
   - I need to instantiate things outside of server.py. Possibly we need a class object to store the 
   instantiated predictor.
   - **Wrote a `Predictor` class which compiles the needed tf graphs. Had to add some functions to `tensorize.py`
   and `convert`. You can now make predictions programmatically using the `Predictor` class.**

New things added so far:
- Added a `download_models` function to utils.py which downloads and extracts the Prosit models into a "models"
directory inside the `prysit` directory (i.e. in `site-packages`)
- Wrote a `spectra_compare` class. This takes the path to an MzML file as input. It has some functions, the most useful
  of which you give a scan number and a peptide sequence (and a collision energy and charge), and it predicts the 
  fragment ions arising from that sequence and calculate the normalized spectra contrast angle between them and the
  actual observed spectrum. Interestingly, you can give it multiple peptides which it scores against the same spectrum
  simultaneously (as if it were a chimeric spectrum). Not sure if that is useful as is, but its interesting.

# Prosit

Prosit is a deep neural network to predict iRT values and MS2 spectra for given peptide sequences. 
You can use it at [proteomicsdb.org/prosit/](http://www.proteomicsdb.org/prosit/) without installation.

[![CLA assistant](https://cla-assistant.io/readme/badge/kusterlab/prosit)](https://cla-assistant.io/kusterlab/prosit)

## Hardware

Prosit requires

- a [GPU with CUDA support](https://developer.nvidia.com/cuda-gpus)


## Installation

Prosit requires

- [Docker 17.05.0-ce](https://docs.docker.com/install/)
- [nvidia-docker 2.0.3](https://github.com/NVIDIA/nvidia-docker) with CUDA 8.0 and CUDNN 6 or later installed
- [make 4.1](https://www.gnu.org/software/make/)

Prosit was tested on Ubuntu 16.04, CUDA 8.0, CUDNN 6 with Nvidia Tesla K40c and Titan Xp graphic cards with the dependencies above.

The time installation takes is dependent on your download speed (Prosit downloads a 3GB docker container). In our tests installation time is ~5 minutes.

## Model

Prosit assumes your models are in directories that look like this:

- model.yml - a saved keras model
- config.yml - a model specifying names of inputs and outputs of the model
- weights file(s) - that follow the template `weights_{epoch}_{loss}.hdf5`

You can download pre-trained models for HCD fragmentation prediction and iRT prediction on https://figshare.com/projects/Prosit/35582.

## Usage

The following command will load your model from `/path/to/model/`.
In the example GPU device 0 is used for computation. The default PORT is 5000.

    make server MODEL_SPECTRA=/path/to/fragmentation_model/ MODEL_IRT=/path/to/irt_model/

Currently two output formats are supported: a MaxQuant style `msms.txt` not including the iRT value and a generic text file (that works with Spectronaut)

## Example

Please find an example input file at `example/peptidelist.csv`. After starting the server you can run the following commands, depending on what output format you prefer:

    curl -F "peptides=@examples/peptidelist.csv" http://127.0.0.1:5000/predict/generic

    curl -F "peptides=@examples/peptidelist.csv" http://127.0.0.1:5000/predict/msp

    curl -F "peptides=@examples/peptidelist.csv" http://127.0.0.1:5000/predict/msms

The examples take about 4s to run. Expected output files (.generic, .msp and .msms) can be found in `examples/`.

## Using Prosit on your data

You can adjust the example above to your own needs. Send any list of (Peptide, Precursor charge, Collision energy) in the format of `/example/peptidelist.csv` to a running instance of the Prosit server.

Please note: Sequences with amino acid U, O, or X are not supported. Modifications except "M(ox)" are not supported. Each C is treated as Cysteine with carbamidomethylation (fixed modification in MaxQuant).

## Pseudo-code

1. Load the models given as in the MODEL\_X environment variables
2. Start a server and wait for inputs
3. On incomming request
    * transform peptide list to model input format (numpy arrays)
    * predict fragment intensity and iRT with the loaded models for the given peptides
    * transform prediction to the requested output format and return response
