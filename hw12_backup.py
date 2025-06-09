#!/usr/bin/env python
# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException
import time
import ddddocr
import base64
from datetime import datetime
import traceback
from selenium.webdriver.common.keys import Keys

# 預約設定
# 場地設定
SPORT_TYPE = "2"           # 運動類型: "2" 為排球
FIELD_CODE = "VOL0D"       # 場地代碼: "VOL0F" 為排球場地F

# 時間設定
RESERVE_DATE = "2025/06/18"   # 要預約的日期 (格式: YYYY/MM/DD)
RESERVE_TIME = "19~21"        # 要預約的時段 (格式: HH~HH)

# 預約者資訊
STUDENT_ID = "411012046"      # 學號
PASSWORD = "42689742ASDfgh"   # 密碼
REASON = "0"                  # 申請理由

def wait_until_time(target_hour, target_minute):
    """等待到指定時間"""
    while True:
        now = datetime.now()
        if now.hour == target_hour and now.minute == target_minute:
            print(f"時間到達 {target_hour:02d}:{target_minute:02d}，開始執行...")
            break
        if (now.hour > target_hour) or (now.hour == target_hour and now.minute > target_minute):
            print(f"已超過預定時間 {target_hour:02d}:{target_minute:02d}，立即執行...")
            break
        if now.second == 0:  # 每分鐘顯示一次等待狀態
            remaining_minutes = (target_hour - now.hour) * 60 + (target_minute - now.minute)
            print(f"還需等待 {remaining_minutes} 分鐘...")
        time.sleep(0.1)

def try_reserve():
    """執行預約程序"""
    success = False
    browser = None
    
    try:
        # 設置 Chrome 選項
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_experimental_option("detach", True)
        
        # 啟動 Chrome
        browser = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(browser, 20)
        
        # 打開預約系統並登入
        browser.get("https://sys.ndhu.edu.tw/gc/sportcenter/SportsFields/login.aspx")
        
        # 輸入帳號密碼
        browser.find_element(By.ID, "MainContent_TxtUSERNO").send_keys(STUDENT_ID)
        browser.find_element(By.NAME, "ctl00$MainContent$TxtPWD").send_keys(PASSWORD)
        browser.find_element(By.ID, "MainContent_Button1").click()

        # 等待頁面載入並設置預約資訊
        wait.until(EC.presence_of_element_located((By.ID, "MainContent_drpkind")))
        print(f"設定欲預約日期: {RESERVE_DATE}")
        
        # 設置運動類型
        browser.execute_script(
            "var typeSelect = document.getElementById('MainContent_drpkind'); typeSelect.value = arguments[0]; __doPostBack('ctl00$MainContent$drpkind','');",
            SPORT_TYPE
        )
        time.sleep(0.5)
        
        # 設置場地
        browser.execute_script(
            "var fieldSelect = document.getElementById('MainContent_DropDownList1'); fieldSelect.value = arguments[0]; __doPostBack('ctl00$MainContent$DropDownList1','');",
            FIELD_CODE
        )
        time.sleep(0.5)
          # 設置預約日期
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # 設置日期
                browser.execute_script(
                    f"var dateInput = document.getElementById('MainContent_TextBox1'); dateInput.removeAttribute('readonly'); dateInput.value = '{RESERVE_DATE}'; __doPostBack('ctl00$MainContent$TextBox1','');"
                )
                time.sleep(0.5)
                
                # 點擊查詢按鈕
                browser.execute_script("__doPostBack('ctl00$MainContent$Button1','')")
                time.sleep(0.5)
                
                # 確認日期
                date_input = wait.until(EC.presence_of_element_located((By.ID, "MainContent_TextBox1")))
                actual_date = date_input.get_attribute('value')
                print(f"確認預約日期: {actual_date}")
                
                # 驗證日期是否正確
                if actual_date == RESERVE_DATE:
                    print("日期設置成功！")
                    break
                else:
                    print(f"日期不符，重試中... ({attempt + 1}/{max_attempts})")
                    if attempt == max_attempts - 1:
                        raise Exception(f"無法設置日期，預期：{RESERVE_DATE}，實際：{actual_date}")
                    time.sleep(0.5)
                    
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise e
                print(f"設置日期失敗，重試中... ({attempt + 1}/{max_attempts})")
                time.sleep(0.5)
        
        print("等待查詢結果...")
        time.sleep(0.5)

        # 點擊新增申請按鈕
        print("準備點擊新增申請按鈕...")
        for attempt in range(3):
            try:
                add_button = wait.until(
                    EC.presence_of_element_located((By.ID, "MainContent_Button2"))
                )
                if not add_button.is_displayed():
                    browser.execute_script("arguments[0].scrollIntoView(true);", add_button)
                    time.sleep(0.5)
                add_button.click()
                
                time_slots = WebDriverWait(browser, 10).until(
                    EC.presence_of_all_elements_located((By.XPATH, "//font[@style='color:green;font-weight:bold;']"))
                )
                if len(time_slots) > 0:
                    print("成功進入時段選擇畫面")
                    break
            except Exception as e:
                print(f"點擊嘗試 {attempt + 1} 失敗: {str(e)}")
                if attempt < 2:
                    browser.refresh()
                    time.sleep(0.5)
                else:
                    raise Exception("無法點擊新增申請按鈕")
        
        # 選擇時段
        print(f"尋找目標時段: {RESERVE_TIME}...")
        time_slots = browser.find_elements(By.XPATH, "//font[@style='color:green;font-weight:bold;']")
        print(f"找到 {len(time_slots)} 個可用時段")
        target_slot = None
        
        all_slots = [slot.text.strip() for slot in time_slots]
        print(f"可用時段列表: {all_slots}")
        
        for slot in time_slots:
            slot_text = slot.text.strip()
            print(f"檢查時段: {slot_text}")
            if RESERVE_TIME == slot_text:
                print(f"找到完全匹配的時段: {slot_text}")
                target_slot = slot
                break
            elif RESERVE_TIME in slot_text:
                print(f"找到包含目標時段的選項: {slot_text}")
                target_slot = slot
                break
        
        if target_slot:
            print(f"準備點擊時段: {target_slot.text}")
            wait.until(EC.element_to_be_clickable((By.XPATH, f"//font[@style='color:green;font-weight:bold;' and contains(text(), '{target_slot.text}')]")))
            target_slot.click()
            time.sleep(0.5)
        else:
            available_times = "\n".join([f"- {slot}" for slot in all_slots])
            raise Exception(f"找不到時段: {RESERVE_TIME}\n可用時段有:\n{available_times}")

        # 處理驗證碼
        print("處理驗證碼...")
        wait.until(EC.presence_of_element_located((By.ID, "imgCaptcha")))
        time.sleep(0.5)
        
        captcha_img = browser.find_element(By.ID, "imgCaptcha")
        img_src = captcha_img.get_attribute('src')
        
        if not img_src or not img_src.startswith('data:image/jpeg;base64,'):
            raise Exception("無法獲取驗證碼圖片數據")
        
        img_base64 = img_src.replace('data:image/jpeg;base64,', '')
        img_data = base64.b64decode(img_base64)
        
        ocr = ddddocr.DdddOcr(show_ad=False)
        captcha_text = ocr.classification(img_data)
        print(f"識別出的驗證碼為: {captcha_text}")
        
        captcha_input = wait.until(
            EC.presence_of_element_located((By.ID, "txtCaptchaValue"))
        )
        captcha_input.clear()
        captcha_input.send_keys(captcha_text)
        time.sleep(0.5)

        # 點擊申請按鈕
        print("點擊申請按鈕...")
        apply_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='申請']"))
        )
        apply_button.click()
        time.sleep(0.5)

        # 填寫申請理由
        reason_input = browser.find_element(By.ID, "MainContent_ReasonTextBox1")
        reason_input.clear()
        reason_input.send_keys(REASON)
        
        # 確認申請
        browser.find_element(By.ID, "MainContent_Button4").click()
        
        success = True
        print("預約完成！")
        
    except Exception as e:
        print(f"發生錯誤: {str(e)}")
        traceback.print_exc()
    
    return success

if __name__ == "__main__":
    try_reserve()
