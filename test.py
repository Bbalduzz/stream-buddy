# https://streamingcommunity.broker/iframe/6962?episode_id=44302&next_episode=1

from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()  # You can also use .firefox or .webkit
    page = browser.new_page()

    # Open the webpage
    page.goto("https://streamingcommunity.broker/iframe/6962?episode_id=44302&next_episode=1")

    # JavaScript code to be injected
    js_code = """
    alert('Hello, World!');
    // You can place any JavaScript code here
    """

    # Injecting the JavaScript code
    page.evaluate(js_code)

    # Optional: Taking a screenshot
    # page.screenshot(path="example.png")

    # browser.close()

with sync_playwright() as playwright:
    run(playwright)
