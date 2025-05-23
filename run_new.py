import argparse
import hashlib
import json
import logging
import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import naver_paper_clien as clien
import naver_paper_damoang as damoang
import naver_paper_ppomppu as ppomppu
import naver_paper_ruliweb as ruliweb


def grep_campaign_links():
    campaign_links = []
    campaign_links += clien.find_naver_campaign_links()
    campaign_links += damoang.find_naver_campaign_links()
    campaign_links += ppomppu.find_naver_campaign_links()
    campaign_links += ruliweb.find_naver_campaign_links()

    if(campaign_links == []):
        print("모든 링크를 방문했습니다.")
        exit()

    return set(campaign_links)


def init(id, pwd, ua, mobile_device, headless, newsave):
    # 크롬 드라이버 옵션 설정
    chrome_options = webdriver.ChromeOptions()

    if headless is True:
        chrome_options.add_argument("--headless=new")
    user_dir = os.getcwd() + "/user_dir/" + hashlib.sha256(f"{id}_{pwd}_{ua}".encode('utf-8')).hexdigest()
    chrome_options.add_argument(f"--user-data-dir={user_dir}")
    if ua is not None:
        chrome_options.add_argument(f"--user-agent={ua}")

    # 새로운 창 생성
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get("https://nid.naver.com")

    # Login page (log-in required) title for nid.naver.com
    #   <title>Naver Sign in</title>
    # ID page (successful logged-in) title for nid.naver.com
    #   <title>Naver ID</title>
    
    time.sleep(30)
    
    if driver.title == "Naver ID" or driver.title == "네이버ID":
        return driver

    # 현재 열려 있는 창 가져오기
    current_window_handle = driver.current_window_handle

    # 새롭게 생성된 탭의 핸들을 찾습니다
    # 만일 새로운 탭이 없을경우 기존 탭을 사용합니다.
    new_window_handle = None
    for handle in driver.window_handles:
        if handle != current_window_handle:
            new_window_handle = handle
            break
        else:
            new_window_handle = handle

    # 새로운 탭을 driver2로 지정합니다
    driver.switch_to.window(new_window_handle)
    driver2 = driver

    username = driver2.find_element(By.NAME, 'id')
    pw = driver2.find_element(By.NAME, 'pw')

    # GitHub Action을 사용하지 않을 경우, 아래와 같이 변경 해주어야 합니다.
    input_id = id
    input_pw = pwd

    # ID input 클릭
    username.click()
    # js를 사용해서 붙여넣기 발동 <- 왜 일부러 이러냐면 pypyautogui랑 pyperclip를 사용해서 복붙 기능을 했는데 운영체제때문에 안되서 이렇게 한거다.
    driver2.execute_script("arguments[0].value = arguments[1]", username, input_id)
    time.sleep(1)

    pw.click()
    driver2.execute_script("arguments[0].value = arguments[1]", pw, input_pw)
    time.sleep(1)

    # Enable Stay Signed in
    if not driver2.find_element(By.CLASS_NAME, "input_keep").is_selected():
        driver2.find_element(By.CLASS_NAME, "keep_text").click()
        time.sleep(1)

    # Enable IP Security
#    if not driver2.find_element(By.CLASS_NAME, "switch_checkbox").is_selected():
#        driver2.find_element(By.CLASS_NAME, "switch_btn").click()
#        time.sleep(1)

    # 입력을 완료하면 로그인 버튼 클릭
    driver2.find_element(By.CLASS_NAME, "btn_login").click()
    time.sleep(100)

    # new.save 등록
    # new.dontsave 등록 안함
#    try:
#        if newsave is True:
#            driver2.find_element(By.ID, "new.save").click()
#        else:
#            driver2.find_element(By.ID, "new.dontsave").click()
#        time.sleep(1)
#    except Exception as e:
#        # Print warning and go to login page.
#        logging.warning("%s: new save or dontsave 오류", e)
#        driver.get("https://nid.naver.com")

    try_login_limit = os.getenv("TRY_LOGIN", 3)
    try_login_count = 1
    while True:
        page_title = driver2.title
        if page_title == "Naver ID" or page_title == "네이버ID":
            break
        if try_login_count > try_login_limit:
            exit()
        print(f"로그인 되지 않음 #{try_login_count}")
        print(f"페이지 타이틀 : {page_title}")

        if headless is True:
            time.sleep(1)
        else:
            # Additional time for the user to address any login issues.
            time.sleep(30)
        try_login_count += 1

    return driver2

def add_options_mobile_device(id, pwd, ua, mobile_device, headless, driver):
    # 현재 URL 저장
    current_url = driver.current_url

    # 새로운 Chrome 옵션 생성
    new_options = webdriver.ChromeOptions()

    # 기존 옵션
    if headless is True:
        new_options.add_argument("--headless=new")
    user_dir = os.getcwd() + "/user_dir/" + hashlib.sha256(f"{id}_{pwd}_{mobile_device}".encode('utf-8')).hexdigest()
    new_options.add_argument(f"--user-data-dir={user_dir}")
    if ua is not None:
        new_options.add_argument(f"--user-agent={ua}")

    # 모바일 에뮬레이션 추가
    if mobile_device:
        mobile_emulation = {"deviceName": mobile_device}
        new_options.add_experimental_option("mobileEmulation", mobile_emulation)

    # 새로운 드라이버 생성
    new_driver = webdriver.Chrome(options=new_options)

    # 쿠키 복사
    new_driver.get(current_url)
    for cookie in driver.get_cookies():
        new_driver.add_cookie(cookie)

    # 기존 드라이버 종료
    driver.quit()
    return new_driver

def alert_accept(alert, drvier):
    try:
        alert.accept()
    except:
        print("일반적인 방법으로 알럿을 닫을 수 없습니다. JavaScript를 사용해 닫기를 시도합니다.")
        drvier.execute_script("window.alert = function() {};")
        drvier.execute_script("window.confirm = function() { return true; };")

def visit(campaign_links, driver2):
    campaign_links_len = len(campaign_links)
    for idx, link in enumerate(campaign_links):
        print(f"\r\n[{idx+1}/{campaign_links_len}] campaign link\t : {link}")
        try:
            # Send a request to the base URL
            driver2.get(link)
            result = driver2.switch_to.alert
            print(f"알럿창\r\n{result.text}")
            if (result.text == "적립 기간이 아닙니다."
                or result.text == "클릭적립은 캠페인당 1회만 적립됩니다."):
                alert_accept(result)
            else:
                time.sleep(4)
                alert_accept(result)
        except:
            try:
                div_dim = driver2.find_element('css selector', 'div.dim')
                print(f"레이어 알럿창\r\n{div_dim.text}")
            except:
                print(f"화면을 불러오지 못했거나 또는 클릭할 수 있는 내용 없음")
                # error_title = driver2.find_element('css selector', 'div.error_title')
                # print(f"{error_title.text}")
                pass
            time.sleep(3)
            # pageSource = driver2.page_source
            # print(pageSource)
        time.sleep(1)


def main(campaign_links, id, pwd, ua, mobile_device, headless, newsave):
    driver = init(id, pwd, ua, mobile_device, headless, newsave)
    if mobile_device is not None:
        driver = add_options_mobile_device(id, pwd, ua, mobile_device, headless, driver)
    visit(campaign_links, driver)
    driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--id', type=str, required=False, help="naver id")
    parser.add_argument('-p', '--pw', type=str, required=False, help="naver password")
    parser.add_argument('-c', '--cd', type=str, required=False, help="credential json")
    parser.add_argument('--headless', type=bool, required=False,
                        default=True, action=argparse.BooleanOptionalAction,
                        help="browser headless mode (default: headless)")
    parser.add_argument('--newsave', type=bool, required=False,
                        default=False, action=argparse.BooleanOptionalAction,
                        help="new save or do not")
    parser.add_argument('-cf', '--credential-file', type=str, required=False,
                        help="credential json file")
    args = parser.parse_args()
    cd_obj = None
    headless = args.headless
    newsave = args.newsave
    if (args.id is None and
            args.pw is None and
            args.cd is None and
            args.credential_file is None):
        id = os.getenv("USERNAME")
        pw = os.getenv("PASSWORD")
        cd_env = os.getenv("CREDENTIALENV", None)
        if(pw is None and pw is None and cd_env is None):
            print('not setting USERNAME / PASSWORD')
            exit()
        if cd_env is None or cd_env == "":
            cd_obj = [{"id": id, "pw": pw}]
        else:
            cd_obj = json.loads(cd_env)
    elif(args.cd is not None):
        try:
            cd_obj = json.loads(args.cd)
        except:
            print('use -c or --cd argument')
            print('credential json sample [{"id":"id1","pw":"pw1"},{"id":"id2","pw":"pw2"}]')
            print('json generate site https://jsoneditoronline.org/')
            exit()
    elif args.credential_file is not None:
        file_obj = open(args.credential_file, "r", encoding="utf-8")
        cd_obj = json.load(file_obj)
    else:
        if args.id is None:
            print('use -i or --id argument')
            exit()
        if args.pw is None:
            print('use -p or --pwd argument')
            exit()
        cd_obj = [{"id": args.id, "pw": args.pw}]

    campaign_links = grep_campaign_links()
    for idx, account in enumerate(cd_obj):
        id = account.get("id")
        pw = account.get("pw")
        ua = account.get("ua")
        mobile_device = account.get("mobile_device")

        print(f"\r\n>>> {idx+1}번째 계정")

        if id is None:
            print("ID not found!")
            continue
        if pw is None:
            print("PW not found!")
            continue

        main(campaign_links, id, pw, ua, mobile_device, headless, newsave)
