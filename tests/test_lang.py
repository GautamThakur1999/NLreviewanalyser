import pytest
from engine.clean.lang import identify_language

def test_language_identification():
    # English
    assert identify_language("This is a great app.") == "en"
    assert identify_language("Delivery was very fast and items were fresh.") == "en"
    
    # Hindi (Devanagari)
    assert identify_language("यह बहुत अच्छा ऐप है।") == "hi"
    assert identify_language("ऐप बेकार है") == "hi"
    
    # Hinglish
    assert identify_language("Bhai yeh app mast hai.") == "hi-Latn"
    assert identify_language("Delivery bohot late aayi yaar") == "hi-Latn"
    assert identify_language("mast app") == "hi-Latn"  # short with 1 word
    assert identify_language("bekar") == "hi-Latn"  # short with 1 word
    assert identify_language("Good app but customer service bekar hai") == "hi-Latn" # mixed
    
    # Empty
    assert identify_language("") == "en"
