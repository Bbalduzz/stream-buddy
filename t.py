import requests
uri = "https://vixcloud.co/playlist/168875?type=audio&rendition=ita&token=FUtlJOY4cHxHmMhbhUpz-w&expires=1707392198&b=1"
c = requests.get(uri).text

print(c)