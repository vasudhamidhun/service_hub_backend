from transformers import pipeline

MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
sentiment_model = pipeline(
    "sentiment-analysis",
    model=MODEL_NAME
) 
def analyze_sentiment(review_text):

    if not review_text or not review_text.strip():
        raise ValueError("Review text cannot be empty")

    result = sentiment_model(review_text)[0]

    # sentiment_model return output like this
    # [ { 'label': 'positive', 'score': 0.998 } ] so the result we want is in [0]

    return {
        "sentiment": result["label"].lower(),
        "confidence": round(result["score"], 4)
    }


# Note
# transformers is a Python library developed by 
# Hugging Face. It allows us to use pretrained machine-learning
#  models for tasks such as sentiment analysis, text classification, 
# translation, summarization and question answering.

# There are two important arguments.
# --------------------------------
# A. "sentiment-analysis" 
# This tells Transformers what task we want to perform.
# It identifies the appropriate pipeline for sentiment classification.
# B. model=MODEL_NAME
# This tells Transformers which pretrained model to load.
# The value:

# cardiffnlp/twitter-roberta-base-sentiment-latest
# is the model's unique repository ID on Hugging Face Hub.

# When you pass this ID, Transformers:
# 1. Looks for that model repository on Hugging Face Hub.
# 2. Downloads its configuration (config.json).
# 3. Downloads the tokenizer files.
# 4. Downloads the pretrained weights (model.safetensors).
# 5. Loads everything into Python.
# 6. Prepares the model to perform sentiment analysis.

#  How does it know which architecture to use
# ----------------------------------------------
# The model's config.json contains information about its architecture.
