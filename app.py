import pandas as pd
from threading import Thread
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from flask import Flask, request, Response, jsonify
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
import random
import json
import urllib
import socket
app = Flask(__name__)
#Scroll Friends All the way 
def scrollFriends(driver):
    time.sleep(random.randint(5, 6))
    driver.get('https://m.facebook.com/friends/center/friends/')
    data = []
    profiles_data = []
    try:
        lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        match=False
        while(match==False):
            soup_friends = BeautifulSoup(driver.page_source, 'html.parser')
            profiles_new = soup_friends.select('#friends_center_main ._52jh._5pxc._8yo0 a')
            lastCount = lenOfPage
            time.sleep(random.randint(5,7))
            lenOfPage = driver.execute_script("window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
            if lastCount==lenOfPage:
                match=True
        soup_friends = BeautifulSoup(driver.page_source, 'html.parser')
        profiles_new = soup_friends.select('#friends_center_main ._52jh._5pxc._8yo0 a')
        urls_dict = {}

        for profile in profiles_new:
            profiles_data.append([f'https://m.facebook.com{profile.get("href")}', profile.getText()])
            urls_dict[f'https://m.facebook.com{profile.get("href")}'] = profile.getText()

        urls_json = json.dumps(urls_dict)
        return profiles_data,urls_json
    except:
        return "Error Scrolling Down"
#Opening Every Profile
def firendsProfile(driver,profiles_data,user_id,c_user):
    for k in range(len(profiles_data)):
        try:
            friend_name = profiles_data[k][1]
            driver.get(profiles_data[k][0])
            time.sleep(2)
            profile_pic_trigger = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, '._42b6._1zet._403j i')))
            profile_pic_trigger.click()
            time.sleep(random.randint(6,9))
            x = WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'i[data-store]'))).get_attribute('data-store')
            y = json.loads(x)
            profile_pic = y['imgsrc']
            print("[] Image URL", profile_pic)
            print("[] Sending to API Endpoint... ")
            post_data = urllib.parse.urlencode({'user_id' : user_id, 'c_user' : c_user, 'profile_holder_name': friend_name, 'profile_holder_image' : profile_pic}).encode()
            req =  urllib.request.Request('https://irvinei.com/api/api/save-list-item',data=post_data)
            resp = urllib.request.urlopen(req)
            data.append([profiles_data[k][0], friend_name, profile_pic])
        except Exception as e:
            print("Execption :: "+str(e))
            continue
def start_scraping(driver,c_user, user_id):
    #Successfully Logged In & started Scrolling Friends
    driver.get(f'https://irvinei.com/api/api/is-sync?is_sync=Yes&userid={user_id}')
    #Response Friends Scroll
    print("[+] Started Scrolling Friends")
    friends_scroll,urls_json=scrollFriends(driver)
    print("[-] Scrolling Friends Done")
    if friends_scroll!="Error Scrolling Down":
        post_data = urllib.parse.urlencode({'c_user' : c_user, 'userid' : int(user_id), 'totalcount': len(friends_scroll), 'linktext' : urls_json}).encode()
        req =  urllib.request.Request('https://irvinei.com/api/api/ScrappingController/lastupdateUserfriends', data=post_data)
        resp = urllib.request.urlopen(req)
        #Extracting Every Friend
        print("[+] Started Getting Friends Profile ")
        firendsProfile(driver,friends_scroll,user_id,c_user)
        print("[-] Profiles Done")
    else:
        print(friends_scroll)
    driver.get(f'https://irvinei.com/api/api/is-sync?is_sync=No&userid={user_id}')
def select_proxy():
    #Proxy 
    data=pd.read_csv("Proxies.csv")
    while True:
        proxy=data["Proxy"][random.randint(0,638)]
        ip,port=proxy.split(":")
        #Checking Proxy
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #Trying to Connect
        try:
            s.connect((ip,int(port)))
            return proxy
            break
        except:
            print(f"[-] Proxy Error {proxy}")
@app.route('/')
def scrape_friends():
    try:
        user_id = request.args.get('user_id')
        c_user = request.args.get('c_user')
        xs = request.args.get('xs')
        datr = request.args.get('datr')

        if c_user == None or xs == None or datr == None or user_id == None:
            return jsonify(
                message='Required parameters not provided'
            )
        proxy=select_proxy()
        print(f"[+] Found Proxy {proxy}")
        # driver
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--log-level=3')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument(f"--proxy-server={proxy}")
        driver = webdriver.Chrome(executable_path=r'./chromedriver.exe', options=chrome_options)
        # driver.maximize_window()
        driver.get('https://m.facebook.com/')

        #Add Cookies
        time.sleep(random.randint(1, 3))
        driver.add_cookie({'name' : 'c_user', 'value' : c_user, 'domain' : '.facebook.com'})
        driver.add_cookie({'name' : 'xs', 'value' : xs, 'domain' : '.facebook.com'})
        driver.add_cookie({'name': 'datr', 'value' : datr, 'domain' : '.facebook.com'})

        driver.get('https://m.facebook.com/friends/center/friends/')
        time.sleep(3)

        if  "Sorry, this content isn't available right now" in driver.page_source:
            try:
                driver.close()
            except:
                pass
            return jsonify(
                user_id=c_user,
                message = 'Unable to login'
            )
        else:
            Thread(target=start_scraping, args=(driver,user_id, c_user,)).start()
            return jsonify(
                user_id=c_user,
                message = 'Login was successful. Scraping has started'
            )

    except Exception as e:
        try:
            driver.close()
        except:
            pass
        print(e)
        return jsonify(
            message='The process failed to start'
        )

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
