from playwright.sync_api import sync_playwright

def authenticate():
    with sync_playwright() as p:
        # Launch a visible browser so you can interact
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto("https://www.linkedin.com/login") # Replace with target directory
        
        print("Please log in manually in the opened browser window.")
        input("Press Enter in this terminal ONCE you are fully logged in...")
        
        # Save the session cookies and local storage
        context.storage_state(path="auth.json")
        print("Session successfully saved to auth.json")
        browser.close()

if __name__ == "__main__":
    authenticate()