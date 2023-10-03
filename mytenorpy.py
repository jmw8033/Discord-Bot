import requests, json, random
import config

apikey = config.TENOR_TOKEN

def search_tenor(message):
    message = '.'.join(e for e in message if e.isalnum())

    get = requests.get("https://tenor.googleapis.com/v2/search?q=%s&key=%s&client_key=%s&limit=%s" % (message, apikey, "test", 15))
    if get.status_code == 200:
        data = json.loads(get.content)
        gif = random.choice(data["results"])
        return gif["url"]
    elif get.status_code == 404:
        return None
    
if __name__ == "__main__":
    print(search_tenor("hi"))