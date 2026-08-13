import os

from optimization.ensemble import SimpleEnsembleModel


ENSEMBLE_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "ensemble_model.joblib",
)
_ENSEMBLE_MODEL = None


def get_ensemble_model():
    global _ENSEMBLE_MODEL

    if _ENSEMBLE_MODEL is None:
        if not os.path.exists(ENSEMBLE_MODEL_PATH):
            raise FileNotFoundError("Ensemble model not found. Generate and train the model first.")

        model = SimpleEnsembleModel(model_dir=os.path.dirname(ENSEMBLE_MODEL_PATH))
        model.load(os.path.basename(ENSEMBLE_MODEL_PATH))
        _ENSEMBLE_MODEL = model

    return _ENSEMBLE_MODEL
