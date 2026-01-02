from better_profanity import profanity

BANNED_WORDS = ["scam", "fraud", "guaranteed returns", "competitor_name"]

def init_safety():
    """Load banned words into profanity filter."""
    profanity.load_censor_words()
    profanity.add_censor_words(BANNED_WORDS)

def validate_content(txt: str):
    """
    Returns True if the text is safe, False otherwise.
    """
    if profanity.contains_profanity(txt):
        return False, "Content contains banned or unsafe language."
    return True, "Content is safe."