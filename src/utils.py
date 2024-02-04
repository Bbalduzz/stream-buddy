import re, requests, configparser

def get_domain(file_path='config.ini'):
    try:
        r = requests.get("https://streamingcommunity.at", allow_redirects=False, timeout=3)
        return r.headers['Location'].removeprefix("https://streamingcommunity.").removesuffix("/")
    except requests.exceptions.ConnectionError:
        config = configparser.ConfigParser()
        config.read(file_path)
        return config['DOMAIN']['updated']

def versioning_control(file_path="config.ini"):
    config = configparser.ConfigParser()
    config.read(file_path)
    current_installed_version = config['VERSION']['local']

    newest_version = re.search(r"local = (\d+\.\d+\.\d+)", requests.get("https://raw.githubusercontent.com/Bbalduzz/stream-buddy/main/config.ini").text)[0].removeprefix("local = ")
    if current_installed_version != newest_version:
        print(f"New version available: {newest_version}")
        return False
