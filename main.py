from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

URL = "https://www.777bigwingame.app/#/"

def get_number_from_hash(hash_string):
    """
    Hash string (ဥပမာ - '...431bb') ထဲက နောက်ဆုံးဂဏန်းကို ထုတ်ယူမယ်
    """
    # Regular Expression နဲ့ နောက်ဆုံး ဂဏန်း (0-9) ကို ရှာမယ်
    # \d က ဂဏန်းကို ဆိုလိုတာ၊ $ က အဆုံးကို ဆိုလိုတာ
    match = re.search(r'(\d)(?=[^0-9]*$)', hash_string)
    
    if match:
        return int(match.group(1))
    return None

def convert_to_big_small(last_digit):
    """
    နောက်ဆုံးဂဏန်းကို Big/Small အဖြစ် ပြောင်းမယ်
    """
    if last_digit is None:
        return "Unknown"
    elif 0 <= last_digit <= 4:
        return "Small"
    else: # 5, 6, 7, 8, 9
        return "Big"

def scrape_hash_history():
    """
    Playwright နဲ့ Website ကို Load ပြီး Hash တွေကို ဖမ်းယူမယ်
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Website က Bot လို့ မထင်အောင် User-Agent ထည့်မယ်
page = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

        # Website ကို သွားပါ
        page.goto(URL, wait_until="domcontentloaded")
        page.wait_for_timeout(5000) # Data တွေ Load ဖို့ စောင့်ပါ

        # Page အပြည့်အစုံ HTML ကို ယူမယ်
        html = page.content()
        browser.close()

    # ==========================================
    # ★★★ HTML ထဲက Hash ကို ရှာဖွေခြင်း ★★★
    # ==========================================
    # ပုံထဲကအတိုင်း Hash တွေက ဒီပုံစံမျိုး ရှိနေတယ်လို့ ယူဆပါတယ်။
    # ဒီ Regular Expression က 'Hash:' ဆိုတဲ့စာကြောင်းနောက်က Hash ကို ဖမ်းပါတယ်။
    # (အကယ်၍ HTML ထဲမှာ ဒီပုံစံနဲ့ မတွေ့ခဲ့ရင် Code ကို ပြင်ရပါမယ်။)
    
    hash_pattern = r'Hash:\s*([a-fA-F0-9]+)'
    found_hashes = re.findall(hash_pattern, html)

    # History (အကြီးအသေး အစီအစဉ်) ကို ဆောက်မယ်
    history = []
    for h in found_hashes:
        last_digit = get_number_from_hash(h)
        if last_digit is not None:
            result = convert_to_big_small(last_digit)
            history.append(result)

    return history

def calculate_prediction(history):
    """
    သင့် Formula အတိုင်း ခန့်မှန်းခြင်း
    """
    if not history or len(history) < 2:
        return "Data မလုံလောက်သေးပါ", 0

    last_result = history[-1]
    
    # နောက်ဆုံး Result က ဘယ်နှခါ ဆက်လာလဲ ရေတွက်မယ်
    count = 1
    for i in range(len(history)-2, -1, -1):
        if history[i] == last_result:
            count += 1
        else:
            break

    prediction = ""
    
    # ★★★ သင့် FORMULA (Hash ဂဏန်းကိုကြည့်ပြီး) ★★★
    if last_result == "Small":
        # အသေး ၂ ခါ ဆက်လာရင် အကြီးထိုး
        if count == 2:
            prediction = "Big"
        # အသေး ၃ ခါ ဆက်လာရင် အသေးဆက်ထိုး
        elif count == 3:
            prediction = "Small"
        else:
            prediction = "Big" # Default (အသေး 1 ခါပဲရှိသေးရင် အကြီးပြန်ထိုး)

    elif last_result == "Big":
        # အကြီး ၂ ခါ ဆက်လာရင် အသေးထိုး
        if count == 2:
            prediction = "Small"
        # အကြီး ၃ ခါ ဆက်လာရင် အကြီးဆက်ထိုး
        elif count == 3:
            prediction = "Big"
        else:
            prediction = "Small" # Default

    return prediction, count

@app.route('/predict', methods=['GET'])
def predict_api():
    # 1. Web မှ Hash နဲ့ History ယူမယ်
    history = scrape_hash_history()
    
    # 2. Formula အတိုင်း တွက်မယ်
    prediction, streak = calculate_prediction(history)

    # 3. JSON Result ပြန်ပို့မယ်
    return jsonify({
        "history": history,        # အရင်က ရလဒ်တွေ (ဥပမာ: ["Small", "Big", "Small"])
        "latest": history[-1] if history else None,
        "streak": streak,          # နောက်ဆုံးရလဒ် ဘယ်နှခါ ဆက်လာလဲ
        "prediction": prediction   # သင့် Formula အရ ခန့်မှန်းချက်
    })

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
