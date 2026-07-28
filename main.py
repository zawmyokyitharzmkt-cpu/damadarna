from flask import Flask, jsonify
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

app = Flask(__name__)

URL = "https://www.777bigwingame.app/#/home/AllLotteryGames/WinTrx?id=4"


def scrape_results():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(5000)

        html = page.content()
        browser.close()

    soup = BeautifulSoup(html, "html.parser")

    results = []

    # Example selector (Change according to website)
    for item in soup.select(".history-item"):
        txt = item.get_text(" ", strip=True)

        if "Big" in txt:
            results.append("Big")
        elif "Small" in txt:
            results.append("Small")

    return results


def predict(history):
    if not history:
        return None

    last = history[-1]

    count = 1
    for i in range(len(history)-2, -1, -1):
        if history[i] == last:
            count += 1
        else:
            break

    if last == "Big":
        if count in [1, 2]:
            return "Small"
        else:
            return "Big"

    if last == "Small":
        if count in [1, 2]:
            return "Big"
        else:
            return "Small"

    return None


@app.route("/predict")
def api():

    history = scrape_results()

    prediction = predict(history)

    return jsonify({
        "history": history,
        "last": history[-1] if history else None,
        "streak": (
            len(history)
            - next(
                (i for i in range(len(history)-1, -1, -1)
                 if history[i] != history[-1]),
                -1
            )
            - 1
        ) if history else 0,
        "prediction": prediction
    })


if __name__ == "__main__":
    app.run(debug=True)