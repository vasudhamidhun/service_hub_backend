# import pandas as pd
# from django.conf import settings
# from pathlib import Path


# DATASET_PATH = Path(settings.BASE_DIR) / "Dataset" / "amazon.csv"


# def load_dataset():

#     if not DATASET_PATH.exists():
#         raise FileNotFoundError(
#             f"Dataset not found: {DATASET_PATH}"
#         )

#     df = pd.read_csv(DATASET_PATH)

#     return df