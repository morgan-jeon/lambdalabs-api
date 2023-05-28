#!/usr/bin/python3
# CoolSMS (https://coolsms.co.kr/)

import requests, time, datetime, uuid, hmac, hashlib, os

try:
    import secrets
    API_KEY = secrets.coolsms
    PHONE_NUMBER = secrets.phone_number
except ImportError:
    API_KEY = (os.environ.get('COOLSMS_API_KEY'), os.environ.get('COOLSMS_ACCESS_KEY'))
    PHONE_NUMBER = os.environ.get('PHONE_NUMBER')
    if not API_KEY:
        print("Error, no Key provided.")
        sys.exit()

assert API_KEY

def unique_id():
    return str(uuid.uuid1().hex)

def get_iso_datetime():
    utc_offset_sec = time.altzone if time.localtime().tm_isdst else time.timezone
    utc_offset = datetime.timedelta(seconds=-utc_offset_sec)
    return datetime.datetime.now().replace(tzinfo=datetime.timezone(offset=utc_offset)).isoformat()

def get_signature(key='', msg=''):
    return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()

def get_headers(api_key='', api_secret_key=''):
    date = get_iso_datetime()
    salt = unique_id()
    data = date + salt
    return {
        'Authorization': 'HMAC-SHA256 ApiKey=' + api_key + ', Date=' + date + ', salt=' + salt + ', signature=' +
                         get_signature(api_secret_key, data),
        'Content-Type': 'application/json; charset=utf-8'
    }

def send_one(data):
    api_key, api_secret = API_KEY
    data['agent'] = {'sdkVersion': 'python/4.2.0', 'osPlatform': 'Windows-10-10.0.22621-SP0 | 3.11.0'}
    return requests.post('https://api.coolsms.co.kr/messages/v4/send', headers=get_headers(api_key, api_secret), json=data)

def send_alert(msg: str, title = "", receiver: str = PHONE_NUMBER):
    assert str(receiver) == receiver
    msg_data = {
                "message": {
                    'to': receiver,
                    'from': '01059400602',
                    'text': msg
                    }
                }
    if title:
        msg_data["message"]["subject"] = title

    return send_one(msg_data).text