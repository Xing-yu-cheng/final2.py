import os
import requests
import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class WeatherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("天氣查詢系統")
        self.root.geometry("800x600")
        
        # 設定天氣項目中英文對照
        self.weather_elements = {
            'Wx': '天氣現象',
            'MaxT': '最高溫度',
            'MinT': '最低溫度',
            'CI': '舒適度',
            'PoP': '降雨機率'
        }
        
        # 設定視窗樣式
        style = ttk.Style()
        style.configure('TLabel', font=('微軟正黑體', 12))
        style.configure('TButton', font=('微軟正黑體', 12))
        style.configure('TCombobox', font=('微軟正黑體', 12))
        
        # 主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 標題
        title_label = ttk.Label(main_frame, text="天氣查詢系統", font=('微軟正黑體', 20, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # 地點選擇
        self.location_label = ttk.Label(main_frame, text="選擇地點：")
        self.location_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.location_var = tk.StringVar()
        self.location_combo = ttk.Combobox(main_frame, textvariable=self.location_var, state='readonly', width=40)
        self.location_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 天氣資訊選擇
        self.element_label = ttk.Label(main_frame, text="選擇查詢項目：")
        self.element_label.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.element_var = tk.StringVar()
        self.element_combo = ttk.Combobox(main_frame, textvariable=self.element_var, state='readonly', width=40)
        self.element_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 查詢按鈕
        self.query_btn = ttk.Button(main_frame, text="查詢", command=self.show_weather)
        self.query_btn.grid(row=3, column=0, columnspan=2, pady=20)
        
        # 結果顯示區域
        self.result_frame = ttk.LabelFrame(main_frame, text="查詢結果", padding="10")
        self.result_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.result_text = tk.Text(self.result_frame, height=15, width=70, font=('微軟正黑體', 12))
        self.result_text.pack(expand=True, fill='both')
        
        # 刷新按鈕
        self.refresh_btn = ttk.Button(main_frame, text="重新整理資料", command=self.refresh_data)
        self.refresh_btn.grid(row=5, column=0, columnspan=2, pady=10)
        
        # 載入資料
        self.refresh_data()
        
    def refresh_data(self):
        try:
            data = self.get_weather_data()
            if 'records' in data:
                self.locations = data['records']['location']
            elif 'cwaopendata' in data:
                self.locations = data['cwaopendata']['dataset']['location']
            else:
                raise ValueError("無法識別的資料格式")
                
            # 更新地點下拉選單
            self.location_names = [loc['locationName'] for loc in self.locations]
            self.location_combo['values'] = self.location_names
            if self.location_names:
                self.location_combo.set(self.location_names[0])
                self.update_elements()
                
        except Exception as e:
            messagebox.showerror("錯誤", f"獲取資料時發生錯誤：{str(e)}")
    
    def update_elements(self, event=None):
        location_name = self.location_var.get()
        if not location_name:
            return
            
        location = next(loc for loc in self.locations if loc['locationName'] == location_name)
        self.elements = location['weatherElement']
        # 轉換成中文顯示
        element_names = []
        self.element_mapping = {}  # 用於儲存中文到原始名稱的映射
        for el in self.elements:
            orig_name = el['elementName']
            # 如果有對應的中文名稱就使用，否則使用原始名稱
            display_name = self.weather_elements.get(orig_name, orig_name)
            element_names.append(display_name)
            self.element_mapping[display_name] = orig_name
            
        self.element_combo['values'] = element_names
        if element_names:
            self.element_combo.set(element_names[0])
    
    def show_weather(self):
        location_name = self.location_var.get()
        display_element_name = self.element_var.get()
        
        if not location_name or not display_element_name:
            messagebox.showwarning("警告", "請選擇地點和查詢項目")
            return
            
        # 使用映射取得原始的英文名稱
        element_name = self.element_mapping[display_element_name]
        location = next(loc for loc in self.locations if loc['locationName'] == location_name)
        element = next(el for el in location['weatherElement'] if el['elementName'] == element_name)
        
        self.result_text.delete('1.0', tk.END)
        self.result_text.insert(tk.END, f"{location_name} 的{display_element_name}：\n\n")
        
        for time_info in element['time']:
            start_time = datetime.fromisoformat(time_info['startTime']).strftime('%Y/%m/%d %H:%M')
            end_time = datetime.fromisoformat(time_info['endTime']).strftime('%Y/%m/%d %H:%M')
            value = time_info['parameter']['parameterName']
            # 對於溫度加上單位
            if element_name in ['MaxT', 'MinT']:
                value += " °C"
            elif element_name == 'PoP':
                value += " %"
            self.result_text.insert(tk.END, f"{start_time} ~ {end_time}：{value}\n")
    
    def get_weather_data(self):
        url = "https://opendata.cwa.gov.tw/fileapi/v1/opendataapi/F-C0032-001?Authorization=CWA-2B4B4FE3-8F9E-4065-B9BA-7B07512FB312&downloadType=WEB&format=JSON"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    root = tk.Tk()
    app = WeatherApp(root)
    # 綁定地點選擇更新
    app.location_combo.bind('<<ComboboxSelected>>', app.update_elements)
    root.mainloop()