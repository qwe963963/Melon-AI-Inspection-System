import cv2

import time

import os

import serial

import numpy as np

import math

import re

from ultralytics import YOLO

import tkinter as tk

from tkinter import filedialog

import csv



# =============================

# 1. 設定區 & 全域變數

# =============================

# 自動定位到目前程式所在的資料夾

# 自動取得目前檔案目錄；若在互動式環境下執行則取得當前工作目錄

try:

    BASE_PATH = os.path.dirname(os.path.abspath(__file__))

except NameError:

    BASE_PATH = os.getcwd()

BEFORE_PATH = os.path.join(BASE_PATH, "detect_before")



# 分開兩個不同模式的儲存資料夾

AFTER_PATH_CAM = os.path.join(BASE_PATH, "detect_after")

AFTER_PATH_PIC = os.path.join(BASE_PATH, "detect_after_photo")



os.makedirs(BEFORE_PATH, exist_ok=True)

os.makedirs(AFTER_PATH_CAM, exist_ok=True)

os.makedirs(AFTER_PATH_PIC, exist_ok=True)



# 分開兩個不同模式的 CSV 記錄檔

CSV_FILE_CAM = os.path.join(BASE_PATH, "log_camera.csv")

CSV_FILE_PIC = os.path.join(BASE_PATH, "log_photo.csv")



# 標題列

for file_path in [CSV_FILE_CAM, CSV_FILE_PIC]:

    if not os.path.exists(file_path):

        with open(file_path, mode='w', newline='', encoding='utf-8-sig') as f:

            writer = csv.writer(f)

            writer.writerow(["Test Time", "Total Weight(g)", "Photo Count", "Detect Count", "Report Filename", "Avg Inference Time(ms)"])



# 載入模型

try:

    model = YOLO("yolov8n_finetune.pt") 

    print("✅ YOLO model loaded successfully!")

except Exception as e:

    print(f"❌ 嚴重錯誤: 載入模型失敗！")

    print(f"詳細原因: {e}")

    print("👉 請檢查 'yolov8n_finetune.pt' 是否放在同一個資料夾。")

    input("按 Enter 鍵結束程式...")

    exit()



# 啟動重量標準

START_WEIGHT_THRESHOLD = 1200



# --- 按鈕座標設定 ---

BTN_START_X1, BTN_START_Y1 = 165, 550

BTN_START_X2, BTN_START_Y2 = 365, 630



BTN_HOME_X1, BTN_HOME_Y1 = 360, 765

BTN_HOME_X2, BTN_HOME_Y2 = 480, 840



BTN_STOP_X1, BTN_STOP_Y1 = 500, 765

BTN_STOP_X2, BTN_STOP_Y2 = 620, 840



BTN_NEXT_X1, BTN_NEXT_Y1 = 640, 765

BTN_NEXT_X2, BTN_NEXT_Y2 = 760, 840



# 狀態旗標

next_button_clicked = False

start_button_clicked = False

stop_button_clicked = False

home_button_clicked = False

arduino_done_flag = False



# 目前系統階段 

system_state = 0 

current_weight = 0.0 

USE_CAMERA = None



# =============================

# 2. 滑鼠回調函式

# =============================

def mouse_handler(event, x, y, flags, param):

    global next_button_clicked, start_button_clicked, stop_button_clicked, home_button_clicked, system_state, current_weight

    

    if event == cv2.EVENT_LBUTTONDOWN:

        if system_state == 0:

            if BTN_START_X1 <= x <= BTN_START_X2 and BTN_START_Y1 <= y <= BTN_START_Y2:

                # 只保留重量判斷

                if current_weight > START_WEIGHT_THRESHOLD:

                    start_button_clicked = True

                    print("🖱️ DETECT button clicked! Starting...")

                else:

                    print("⛔ Weight insufficient! Cannot start.")



        elif system_state == 2:

            if BTN_HOME_X1 <= x <= BTN_HOME_X2 and BTN_HOME_Y1 <= y <= BTN_HOME_Y2:

                home_button_clicked = True

            elif BTN_STOP_X1 <= x <= BTN_STOP_X2 and BTN_STOP_Y1 <= y <= BTN_STOP_Y2:

                stop_button_clicked = True

            elif BTN_NEXT_X1 <= x <= BTN_NEXT_X2 and BTN_NEXT_Y1 <= y <= BTN_NEXT_Y2:

                next_button_clicked = True



# =============================

# 3. Serial 連線

# =============================

try:

    ser = serial.Serial("COM3", 115200, timeout=0.1)

    time.sleep(2)

    print("✅ Arduino connected successfully (COM3)")

except Exception as e:

    ser = None

    print(f"❌ Arduino 連線失敗: {e}")



# =============================

# 4. 輔助函式 

# =============================

def sync_hardware():

    global current_weight, arduino_done_flag

    if ser is None: return

    

    if ser.in_waiting > 100: 

        ser.reset_input_buffer()

    

    while ser.in_waiting > 0:

        try:

            line = ser.readline().decode('utf-8', errors='ignore').strip()

            

            # 1. 抓取重量

            if "WEIGHT:" in line:

                match = re.search(r'WEIGHT:\s*([\d\.]+)', line)

                if match:

                    val = float(match.group(1))

                    if val < 10: val = 0

                    current_weight = val



            # 2. 抓取 Arduino 完成訊號

            if "DONE" in line:   

                arduino_done_flag = True

                

        except Exception as e: 

            pass



def draw_ui_waiting(img, weight):

    h, w = img.shape[:2]

    cv2.rectangle(img, (0, 0), (w, 80), (0, 0, 0), -1)

    cv2.circle(img, (35, 40), 10, (0, 255, 255), -1) 

    cv2.putText(img, "SYS: IDLE", (60, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    

    # 顯示重量

    w_col = (0, 255, 0) if weight > START_WEIGHT_THRESHOLD else (0, 0, 255)

    cv2.putText(img, f"WEIGHT: {weight:.0f}g", (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, w_col, 2)

    

    # 只要重量到達即變亮綠色按鈕

    if weight > START_WEIGHT_THRESHOLD:

        btn_color, btn_text_col, status_text = (0, 200, 0), (255, 255, 255), "READY TO START"

    else:

        btn_color, btn_text_col, status_text = (100, 100, 100), (180, 180, 180), "PLEASE ADD WEIGHT"



    cv2.rectangle(img, (BTN_START_X1, BTN_START_Y1), (BTN_START_X2, BTN_START_Y2), btn_color, -1) 

    cv2.rectangle(img, (BTN_START_X1, BTN_START_Y1), (BTN_START_X2, BTN_START_Y2), (255, 255, 255), 2) 

    font = cv2.FONT_HERSHEY_SIMPLEX

    (tw, th), _ = cv2.getTextSize("DETECT", font, 1.2, 3)

    cv2.putText(img, "DETECT", (BTN_START_X1 + (200 - tw) // 2, BTN_START_Y1 + (80 + th) // 2), font, 1.2, btn_text_col, 3)

    cv2.putText(img, status_text, (BTN_START_X1 - 10, BTN_START_Y2 + 30), font, 0.5, btn_color, 2)



def draw_ui_scanning(img, weight, info_text=""):

    h, w = img.shape[:2]

    cv2.rectangle(img, (0, 0), (w, 80), (0, 0, 0), -1)

    cv2.circle(img, (35, 40), 10, (0, 0, 255), -1) 

    cv2.putText(img, "SYS: BUSY", (60, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    

    cv2.putText(img, f"WEIGHT: {weight:.0f}g", (250, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.putText(img, info_text, (500, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)



def draw_scanning_line(img, count):

    h, w = img.shape[:2]

    line_y = (count * 20) % h

    cv2.line(img, (0, line_y), (w, line_y), (0, 255, 255), 2)



def choose_mode():

    global USE_CAMERA

    root = tk.Tk()

    root.title("Mode Selection") 

    root.geometry("350x150")

    root.attributes('-topmost', True) 

    tk.Label(root, text="Please select a test mode:", font=("Arial", 12, "bold")).pack(pady=15)

    

    def set_camera(): global USE_CAMERA; USE_CAMERA = True; root.destroy() 

    def set_photo(): global USE_CAMERA; USE_CAMERA = False; root.destroy() 



    btn_frame = tk.Frame(root)

    btn_frame.pack()

    tk.Button(btn_frame, text="📷 Camera Mode\n(Hardware Req.)", font=("Arial", 10), bg="#c8e6c9", width=16, height=3, command=set_camera).pack(side=tk.LEFT, padx=10)

    tk.Button(btn_frame, text="🖼️ Photo Mode\n(Software Only)", font=("Arial", 10), bg="#bbdefb", width=16, height=3, command=set_photo).pack(side=tk.RIGHT, padx=10)

    

    root.eval('tk::PlaceWindow . center')

    root.mainloop()



# 設定裁切範圍

crop_x, crop_y, crop_w, crop_h = 950, 220, 530, 720 



# =============================

# 5. 主程式迴圈 

# =============================

return_home = True  

cap = None



while True:  

    if return_home:

        if cap: 

            cap.release()

            cap = None

        cv2.destroyAllWindows()

        

        USE_CAMERA = None

        choose_mode()  



        if USE_CAMERA is None:

            print("❌ 未選擇模式，系統安全關閉。")

            if ser: ser.close()

            exit()

        if USE_CAMERA:

            print("🔄 Initializing camera...")

            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

            if not cap.isOpened(): cap = cv2.VideoCapture(0)

            if not cap.isOpened():

                print("⚠️ 找不到攝影機！自動退回選單。")

                continue 

                

            # 💡 關鍵修正：強制要求攝影機使用 MJPG 格式傳輸

            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)

            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

            print("🚀 (Camera Mode) Ready to start!")

        else:

            print("🚀 (Photo Mode) Ready to start!")



        cv2.namedWindow("Main")

        cv2.setMouseCallback("Main", mouse_handler)

        cv2.moveWindow("Main", 1120, 0) 

        

        return_home = False 

    

    next_button_clicked = False

    start_button_clicked = False

    stop_button_clicked = False

    home_button_clicked = False

    images = []

    current_weight = 0.0

    frame_counter = 0



    if USE_CAMERA:

        print("\n⏳ Waiting for weight and click DETECT...")

        system_state = 0 



        while True:

            ret, frame = cap.read()

            if not ret: break

            

            sync_hardware()

            frame = cv2.flip(frame, 1)

            crop = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w] if (crop_y+crop_h < frame.shape[0] and crop_x+crop_w < frame.shape[1]) else frame

            show = crop.copy()



            draw_ui_waiting(show, current_weight)

            

            if start_button_clicked:

                cv2.rectangle(show, (BTN_START_X1, BTN_START_Y1), (BTN_START_X2, BTN_START_Y2), (0, 255, 0), -1)

                cv2.imshow("Main", show)

                cv2.waitKey(1)

                time.sleep(0.3)

                break 

            

            cv2.imshow("Main", show)

            

            key = cv2.waitKey(1) & 0xFF

            if key == 27:

                stop_button_clicked = True

                break

                

        if stop_button_clicked: break 



        system_state = 1

        final_weight = current_weight

        print(f"📸 Taking photos... (Weight: {final_weight})")

        

        shot_count = 0

        max_shots = 4

        next_time = time.time() + 1.0  

        

        waiting_for_arduino = False 

        arduino_timeout = 0         



        while shot_count < max_shots:

            ret, frame = cap.read()

            if not ret: break

            

            sync_hardware() 

            

            frame = cv2.flip(frame, 1)

            crop = frame[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w] if (crop_y+crop_h < frame.shape[0] and crop_x+crop_w < frame.shape[1]) else frame

            show = crop.copy()

            

            draw_scanning_line(show, frame_counter)

            frame_counter += 1

            

            # --- 握手同步等待區 ---

            if waiting_for_arduino:

                draw_ui_scanning(show, final_weight, f"WAITING ARDUINO... {max(0, arduino_timeout - time.time()):.1f}s")

                

                if arduino_done_flag:

                    print("✅ Arduino DONE signal received, preparing next shot!")

                    waiting_for_arduino = False

                    arduino_done_flag = False 

                    next_time = time.time() + 0.5 

                

                elif time.time() > arduino_timeout:

                    print("⚠️ 等待 Arduino 逾時，強制繼續！")

                    waiting_for_arduino = False

                    arduino_done_flag = False

                    next_time = time.time() + 0.5

            

            # --- 拍照與發送命令區 ---

            else:

                draw_ui_scanning(show, final_weight, f"SHOT {shot_count+1}/{max_shots}.. {(next_time - time.time()):.1f}s")

                

                if time.time() >= next_time:

                    fname = f"raw_{time.strftime('%H%M%S')}_{shot_count+1}.jpg"

                    cv2.imwrite(os.path.join(BEFORE_PATH, fname), crop)

                    images.append(crop)

                    

                    if shot_count < 3 and ser:

                        ser.reset_input_buffer() 

                        arduino_done_flag = False 

                        ser.write(b"GO\n")

                        print("📤 已發送轉動訊號 GO")

                        waiting_for_arduino = True           

                        arduino_timeout = time.time() + 15.0 

                        

                    shot_count += 1

                    if not waiting_for_arduino:

                        next_time = time.time() + 1.0 



            cv2.imshow("Main", show)

            if cv2.waitKey(1) & 0xFF == 27: break

    else:

        root = tk.Tk()

        root.withdraw() 

        root.attributes('-topmost', True) 

        

        file_paths = filedialog.askopenfilenames(

            title="Select Test Images (Hold Ctrl to select 1-4 images)",

            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]

        )

        root.destroy() 

        

        if not file_paths:

            print("⚠️ 取消選擇照片，返回首頁...")

            return_home = True

            continue 

            

        file_paths = file_paths[:4]

        for path in file_paths:

            img = cv2.imread(path)

            if img is not None and img.size > 0:

                crop = img[crop_y:crop_y+crop_h, crop_x:crop_x+crop_w] if (crop_y+crop_h < img.shape[0] and crop_x+crop_w < img.shape[1]) else img

                images.append(crop)

                

        final_weight = 0 



    # --------------------------------------------------

    # 產生報告與按鈕判定區

    # --------------------------------------------------

    system_state = 2 

    

    if len(images) > 0:

        actual_photo_count = len(images) 

        print(f"🔍 Generating report for {actual_photo_count} photos...")

        

        processed_imgs = []

        total_sum = 0

        total_inference_time = 0 

        TW, TH = 400, 370 

        

        for i in range(actual_photo_count):

            temp_img = images[i].copy()

            

            start_t = time.time()

            results = model(temp_img, verbose=False, conf=0.75, iou=0.5)[0]

            end_t = time.time()

            total_inference_time += (end_t - start_t)

            

            mask = np.zeros((temp_img.shape[0], temp_img.shape[1]), dtype=np.uint8)



            for box in results.boxes:

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1) 



            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)



            count = len(contours)

            total_sum += count

            

            cv2.drawContours(temp_img, contours, -1, (0, 255, 0), 2)

                

            cv2.putText(temp_img, f"Image: {i+1}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            processed_imgs.append(cv2.resize(temp_img, (TW, TH)))



        avg_time_ms = (total_inference_time / actual_photo_count) * 1000



        blank_img = np.zeros((TH, TW, 3), dtype=np.uint8)

        while len(processed_imgs) < 4:

            processed_imgs.append(blank_img)



        top_row = np.hstack((processed_imgs[0], processed_imgs[1]))

        bottom_row = np.hstack((processed_imgs[2], processed_imgs[3]))

        grid_img = np.vstack((top_row, bottom_row))



        final_name = f"Result_{time.strftime('%H%M%S')}.jpg"

        save_folder = AFTER_PATH_CAM if USE_CAMERA else AFTER_PATH_PIC

        save_csv = CSV_FILE_CAM if USE_CAMERA else CSV_FILE_PIC



        try:

            current_time_str = time.strftime('%Y-%m-%d %H:%M:%S')

            with open(save_csv, mode='a', newline='', encoding='utf-8-sig') as f:

                writer = csv.writer(f)

                writer.writerow([current_time_str, final_weight, actual_photo_count, total_sum, final_name, f"{avg_time_ms:.1f}"])

            print(f"📊 Data written to {os.path.basename(save_csv)}.")

        except Exception as e:

            print(f"⚠️ 寫入 CSV 失敗: {e}")



        # --- 介面面板 ---

        info_panel = np.zeros((120, grid_img.shape[1], 3), dtype=np.uint8)

        info_panel[:] = (50, 50, 50) 

        font = cv2.FONT_HERSHEY_SIMPLEX



        if total_sum > 5:

            result_text = "FAIL"        

            result_color = (0, 0, 255)  

        else:

            result_text = "PASS"        

            result_color = (0, 255, 0)  

            

        cv2.putText(info_panel, f"TOTAL COUNT: {total_sum}", (20, 45), font, 0.8, (255, 255, 255), 2)

        cv2.putText(info_panel, result_text, (235, 80), font, 1.5, result_color, 4)



        if USE_CAMERA: 

            cv2.putText(info_panel, f"WEIGHT: {final_weight}g", (20, 80), font, 0.7, (200, 200, 200), 1)

        cv2.putText(info_panel, f"SPEED: {avg_time_ms:.0f} ms/img", (20, 110), font, 0.5, (0, 255, 255), 1)



        # 顯示底部按鈕

        y1_btn, y2_btn = BTN_HOME_Y1 - grid_img.shape[0], BTN_HOME_Y2 - grid_img.shape[0]

        cv2.rectangle(info_panel, (BTN_HOME_X1, y1_btn), (BTN_HOME_X2, y2_btn), (150, 100, 100), -1)

        cv2.putText(info_panel, "HOME", (BTN_HOME_X1 + 15, y1_btn + 55), font, 1.0, (255, 255, 255), 2)



        cv2.rectangle(info_panel, (BTN_STOP_X1, y1_btn), (BTN_STOP_X2, y2_btn), (0, 0, 200), -1)

        cv2.putText(info_panel, "STOP", (BTN_STOP_X1 + 20, y1_btn + 55), font, 1.0, (255, 255, 255), 2)



        cv2.rectangle(info_panel, (BTN_NEXT_X1, y1_btn), (BTN_NEXT_X2, y2_btn), (255, 100, 0), -1)

        cv2.putText(info_panel, "NEXT", (BTN_NEXT_X1 + 20, y1_btn + 55), font, 1.0, (255, 255, 255), 2)



        final_show = np.vstack((grid_img, info_panel))

        cv2.imwrite(os.path.join(save_folder, final_name), final_show)

        cv2.imshow("Main", final_show)

        

        while not (next_button_clicked or stop_button_clicked or home_button_clicked):

            if cv2.waitKey(100) == 27: stop_button_clicked = True



        if stop_button_clicked:

            if cap: cap.release()  

            cv2.destroyAllWindows()

            if ser: ser.close()

            exit()

        elif home_button_clicked:

            return_home = True  

            continue

