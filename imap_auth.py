import json, pickle, time, subprocess, sys
sys.path.append("lib")
#local files
import oauth2
def makeIMAPAuthString():
    #load client_id and client_secret from local config file
    #expects config file with JSON Blob
    #{"CLIENT_ID":"YOUR CLIENT ID","CLIENT_SECRET":"YOUR CLIENT SECRET"}
    config = json.load(open("config","r"))
    #persistent keystore for saving user auth tokens, etc..
    keys = {}
    keysFile = None
    try:
        keysFile = open("userdata","r+")
        keys = pickle.load(keysFile)
    except IOError:
        keysFile = open("userdata","w")
    #generate auth token for account
    print('Enter full gmail account name, ie. test@gmail.com')
    user_name = raw_input("Username: ")
    
    access_token = ""
    if keys.get(user_name):
        user_data = keys[user_name]
        if time.time() > float(user_data["timestamp"]) + float(user_data["expires_in"]):
            response = oauth2.RefreshToken(config["CLIENT_ID"], config["CLIENT_SECRET"], 
                                           user_data["refresh_token"])
            access_token = response['access_token']
            user_data["expires_in"] = response["expires_in"]
            user_data["access_token"] = response["access_token"]
            user_data["timestamp"] = time.time()
            keys[user_name] = user_data
        else: 
            access_token = user_data['access_token']
    else:
        print('To authorize token, visit this url and follow the directions:')
        url = oauth2.GeneratePermissionUrl(config["CLIENT_ID"])
        xsel_proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        xsel_proc.communicate(url)
        print "URL has been added to clipboard (mac only -- otherwise copy/paste)"
        print '  %s' % url
        authorization_code = raw_input('Enter verification code: ')    
        response = oauth2.AuthorizeTokens(config["CLIENT_ID"], config["CLIENT_SECRET"],
                                authorization_code)
        response['timestamp'] = time.time()
        keys[user_name] = response
        access_token = response['access_token']
        #generate auth string
    auth_string = oauth2.GenerateOAuth2String(user_name, access_token, 
                                              base64_encode=False)
    print(keys)
    pickle.dump(keys,keysFile)
    return (user_name,auth_string)
