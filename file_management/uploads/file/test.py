import requests 
greenweburl = "http://api.greenweb.com.bd/api.php"

# your token code here 
token = "17751359451705046385d681c28af1f6d6ba4dc9289ca664edf6"

# sms receivers number here (separated by comma) 
# to = '+88017xxxxxxx,+88016xxxxxxxx' 
to = '+8801780208855' 

data = {
    'token':token, 
    'to':to, 
    'message':'Hello, This is a test sms by papel from greenweb'
    } 
 
responses = requests.post(url = greenweburl, data = data) 

# response 
print(responses.status_code)
response = responses.text 
print(response) 
