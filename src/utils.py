import re, requests, configparser

def update_domain():
    r = requests.get("https://streamingcommunity.at", allow_redirects=False)
    return r.headers['Location'].removeprefix("https://streamingcommunity.").removesuffix("/")

def versioning_control(file_path="config.ini"):
    config = configparser.ConfigParser()
    config.read(file_path)
    current_installed_version = config['VERSION']['local']

    newest_version = re.search(r"local = (\d+\.\d+\.\d+)", requests.get("https://raw.githubusercontent.com/Bbalduzz/stream-buddy/main/config.ini").text)[0].removeprefix("local = ")
    if current_installed_version != newest_version:
        print(f"New version available: {newest_version}")
        return False