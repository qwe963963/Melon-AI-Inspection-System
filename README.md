# AI 視覺：哈密瓜自動化裂紋與重量偵測系統
**AI-Powered Edge Inspection System with Hardware-Software Handshake Protocol**

此專題為一套結合影像偵測（YOLOv8）、HX711 重量感應與 Arduino 旋轉機構的自動化辨識系統。
透過雙向握手協定（Handshake Protocol），實現「自動秤重 ➔ 旋轉拍照 ➔ 缺陷辨識 ➔ 數據彙整」的全流程檢測系統。

---

## 系統檢測成果 (Inspection Demo)

<p align="center">
  <img src="assets/melon_detection_demo.jpg" width="700" alt="哈密瓜多角度瑕疵偵測成果"><br>
  <sub><b>圖：系統多角度旋轉拍照、YOLOv8 瑕疵標註與數據彙整畫面</b></sub>
</p>

> 💡 **檢測成果說明**：
> * **全方位檢測**：透過旋轉平台拍攝哈密瓜四個面，解決實物為3D之情形。
> * **瑕疵標記與統整**：自動計算哈密瓜實總瑕疵數。
> *( 註：因農作物季節限制，上圖為開發階段使用實體哈密瓜之完整辨識結果。最新版本的UI已不同，而其餘與現階段無誤

---

### 系統架構與技術 (Tech Stack)

* **Libraries (函式庫)**：`Ultralytics YOLOv8` (AI偵測)、`OpenCV` (影像處理與 MJPG 強制解碼)、`PySerial` (雙向連結)、`HX711.h` (重量感應)
* **Systems (核心系統與 UI 介面)**：Python 3.x (主控)、Tkinter GUI (現場圖形操作介面)、CSV 自動化日誌 (檢測數據報表)、Arduino (.ino) (控制馬達轉動與重量讀取)
* **Hardware (實體硬體與感測器)**：Arduino Uno (主控板)、HX711 Load Cell (重量感應模組)、旋轉直流馬達、1080p HD WebCam (高清視覺鏡頭)

---

### 軟硬體雙向握手協定 (Handshake Protocol)

採用比傳統延遲等待還穩定的雙向應答機制，解決實體機構運作時的外在因素干擾（重量）。
系統透過 USB 序列埠 (Baud 115200) 建立 Python（軟體端）與 Arduino（硬體端）之間的溝通機制：

| 方向 | 傳輸字串/指令 | 觸發時間與簡述 |
| :--- | :--- | :--- |
| **Arduino ➔ Python** | `SYSTEM_READY` | Arduino 在 `setup()` 完成 HX711 初始化與校正（Tare）後發送，通知 Python 硬體已就緒。 |
| **Arduino ➔ Python** | `WEIGHT:<value>` | Arduino 每 2 秒回傳重量，Python 即時更新 `current_weight`。 |
| **Python ➔ Arduino** | `GO\n` | Python 完成當前角度拍照並存檔後（`shot_count < 3`），發送指令觸發 Arduino 馬達旋轉平台。 |
| **Arduino ➔ Python** | `DONE\n` | Arduino 馬達旋轉到位後回傳，Python 解析到 `DONE` 後進行下一次拍照。此套流程重複三次，共拍攝四個面。 |

---

### 系統優化與工程亮點 (Engineering Highlights)

本專題針對實體環境變因進行了多項系統調校，確保檢測流程的穩定性與精準度：
* **軟硬體同步 (Delay ➔ Handshake Protocol)**：捨棄傳統時間延遲 (sleep) 機制，使用雙向握手協定，解決軟硬體時間匹配與物理重量干擾問題。
* **瑕疵框重複過濾 (Bounding Box Deduplication)**：針對辨識時同一照片部分瑕疵重複計算問題，使用距離與重疊度過濾邏輯（類似 NMS 概念），去除冗餘標註，提升視覺介面清晰度與數據統計精準度。
* **實體邊界條件與防呆保護**：實作 15 秒 Timeout 異常跳出機制、重量清零門檻（<10g 自動歸零）以及轉盤 ROI 視覺區域裁切，確保現場運作的極致穩定。

---

## 啟動條件 (How to Run)


###  Python 軟體端設定


<details>
<summary><b> 點此展開「詳細環境安裝與啟動步驟 」</b></summary>



**專案結構 (Project Structure)**

```text
Melon-AI-Inspection-System/
├── arduino-hardware/                 # Arduino 韌體專案資料夾 (包含 .ino 燒錄檔)
├── python-software.py                # Python 主控程式 (UI、影像辨識與 Serial 通訊)
├── yolov8n_finetune.pt               # [關鍵] 核心 AI 權重：微調訓練後的哈密瓜瑕疵辨識模型
├── yolov8n.pt                        # 預設/備用 YOLOv8 Nano 基礎權重
│
├── 📁 系統自動建立之輸出目錄 (Outputs)
│   ├── detect_before/                # 原始拍攝影像備份
│   ├── detect_after/                 # 相機即時檢測之 AI 標註結果圖
│   └── detect_after_photo/           # 單張照片測試模式之 AI 標註結果圖
│
└── 📁 系統自動建立之紀錄檔 (Logs)
    ├── log_camera.csv                # 相機檢測模式之數據紀錄報表
    └── log_photo.csv                 # 照片測試模式之數據紀錄報表
```

**環境安裝 (Dependencies)**

請先安裝系統所需的 Python 核心套件：
```bash
pip install ultralytics opencv-python pyserial numpy
```

**執行方式 (How to Run)**

開啟終端機 (Terminal / Command Prompt)，執行主控程式：
```bash
python python-software.py
```

</details>

---

###  Arduino 硬體端設定

本專案使用 Arduino 搭配紅色 HX711 秤重模組讀取重量，並透過 Serial 接收 Python 訊號控制馬達驅動板來帶動轉盤。

<details>
<summary><b> 點此展開「硬體詳細配線方式」</b></summary>



* **開發板**：Arduino Uno (含擴充板，接腳標示為 G=負極 / V=正極 / S=訊號)
* **紅色秤重模組 (HX711)**：
  * DOUT 接擴充板 **D6 的 S 腳位**
  * SCK 接擴充板 **D7 的 S 腳位**
  * VCC 接擴充板的 **V 腳位 (正極)**
  * GND 接擴充板的 **G 腳位 (負極)**
* **紅色馬達控制板 (如 L298N 模組)**：
  * 控制訊號線接擴充板 **D11 的 S 腳位** (支援 PWM)
  * 轉盤馬達連接至控制板側邊的藍色接線端子
  * 下方的藍色端子需連接獨立電源與 GND，以提供馬達足夠動力

**軟體安裝**
請在 Arduino IDE 的「管理函式庫」中搜尋並安裝以下套件：
* `HX711 Arduino Library`

**執行方式**
1. 將 Arduino 連接至電腦，在 IDE 選擇對應的開發板與連接埠。
2. 點擊 **「上傳」** 將程式燒錄至 Arduino。
3. 開啟「序列埠監控器 (Serial Monitor)」，**將 Baud rate 設為 `115200`**。
   * 系統每 2 秒會自動回報 `WEIGHT:數值`。
   * 在輸入框發送 `GO`，馬達即會轉動 1 秒並回傳 `DONE`。

</details>
