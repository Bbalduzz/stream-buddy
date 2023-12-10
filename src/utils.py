import re, requests, configparser

def get_domain_from_ini(file_path='config.ini'):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config['DOMAIN']['updated']

def versioning_control(file_path="config.ini"):
    config = configparser.ConfigParser()
    config.read(file_path)
    current_installed_version = config['VERSION']['local']

    newest_version = re.search(r"local = (\d+\.\d+\.\d+)", requests.get("https://raw.githubusercontent.com/Bbalduzz/stream-buddy/main/config.ini").text)[0]
    if current_installed_version != newest_version:
        print(f"New version available: {newest_version}")
        return False