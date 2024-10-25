url = "https://www.zillow.com/homedetails/2745-N-Maplewood-Ave-Chicago-IL-60647/3669405_zpid/"


from selenium import webdriver
chrome_options = webdriver.ChromeOptions()
chrome_options.set_capability(
                        "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
                    )
driver = webdriver.Chrome(options=chrome_options)


##visit your website, login, etc. then:
log_entries = driver.get_log("performance")

for entry in log_entries:

    try:
        obj_serialized: str = entry.get("message")
        obj = json.loads(obj_serialized)
        message = obj.get("message")
        method = message.get("method")
        if method in ['Network.requestWillBeSentExtraInfo' or 'Network.requestWillBeSent']:
            try:
                for c in message['params']['associatedCookies']:
                    if c['cookie']['name'] == 'authToken':
                        bearer_token = c['cookie']['value']
            except:
                pass
        print(type(message), method)
        print('--------------------------------------')
    except Exception as e:
        raise e from None