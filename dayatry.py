from sentence_transformers import CrossEncoder

# Load the model globally to avoid reloading on each call
model = CrossEncoder('cross-encoder/stsb-roberta-base')

def is_semantically_matching(str1: str, str2: str, threshold: float = 0.75) -> int:
    """
    Returns 1 if str1 and str2 are semantically matching, else 0.
    """
    score = model.predict([(str1, str2)])[0]
    print(f"Score: {score}")
    return int(score > threshold)



print(is_semantically_matching("IIT JAMMU","indian institute of technology jammu"))  # Should return 1