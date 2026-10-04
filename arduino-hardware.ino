#include "HX711.h"

// --- 接腳設定 ---
const int LOADCELL_DOUT_PIN = 6;
const int LOADCELL_SCK_PIN = 7;
HX711 scale;

// ⚠️ 校正參數
float calibration_factor = 300.0;

// ★ 用來記錄上次傳送重量的時間 ★
unsigned long lastWeightTime = 0;

void setup(void) {
  Serial.begin(115200);
  while (!Serial) delay(10);

  pinMode(11, OUTPUT); // ★ 確保馬達腳位(11)設定為輸出 ★

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor);
  scale.tare();
  
  Serial.println("SYSTEM_READY");
}

void loop(void) {
  // 1. 讀取重量 (每 2 秒回報一次)
  if (millis() - lastWeightTime > 2000) {
    if (scale.is_ready()) {
      float currentWeight = scale.get_units();
      
      if (currentWeight <= 0) {
        currentWeight = 0;
      }
      Serial.print("WEIGHT:");
      Serial.println(currentWeight, 1);
      
      lastWeightTime = millis(); // 更新計時器時間
    }
  }

  // 2. 接收 Python 訊號 (★ 隨時聽命！ ★)
  if (Serial.available()) {
    // 改用 readStringUntil，讀到換行 \n 就馬上執行，速度飛快！
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "GO") {
      Serial.print("CMD:");
      Serial.println(cmd);  // 👀 除錯用
      
      // 轉盤轉動 1 秒 (這裡的 delay 是必要的，讓馬達有時間轉)
      analogWrite(11, 255);
      delay(1000);
      analogWrite(11, 0);

      Serial.println("DONE");
    }
  }
  
  // 縮短一般迴圈延遲，讓整體反應更敏捷
  delay(20);
}