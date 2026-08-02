import pytest
from pathlib import Path
from engine.clean.spam import check_spam

def test_spam_filtering():
    fixture_path = Path(__file__).parent / "fixtures" / "spam_samples.txt"
    lines = fixture_path.read_text(encoding="utf-8").splitlines()
    
    # 0: This app is soooooo good, I love it.
    # 1: This app is soooooooooooooooo good, I love it.
    # 2: Please use my code X1234 to get 50 off.
    # 3: I did not get the referral bonus when I signed up.
    # 4: Check out this site http://spam.com for free money.
    # 5: I love shopping at www.amazon.in for groceries.
    # 6: This is a normal review with Rs 50 off mentioned.
    # 7: Please download using code MYCODE.
    # 8: They promised Rs 50 off but gave nothing, bc!
    
    assert check_spam(lines[0]) is None
    assert check_spam(lines[1]) == "spam_bot_repeating_chars"
    assert check_spam(lines[2]) == "spam_bot_promo"
    assert check_spam(lines[3]) is None
    assert check_spam(lines[4]) == "spam_bot_url"
    assert check_spam(lines[5]) == "spam_bot_url"
    assert check_spam(lines[6]) is None
    assert check_spam(lines[7]) == "spam_bot_promo"
    assert check_spam(lines[8]) is None
