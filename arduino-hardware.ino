#include "HX711.h"

// --- 腳位與常數設定 ---
const int LOADCELL_DOUT_PIN = 6;
const int LOADCELL_SCK_PIN = 7;
const int MOTOR_PIN = 11;

HX711 scale;

// --- 系統變數 ---
float calibration_factor = 300.0;
unsigned long lastWeightTime = 0;

void setup(void) {
  Serial.begin(115200);
  while (!Serial) delay(10);

  // 初始化馬達控制腳位
  pinMode(MOTOR_PIN, OUTPUT);

  // 初始化 HX711 秤重模組並執行歸零 (Tare)
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor);
  scale.tare();
  
  // 通知 Python 軟體端硬體已就緒
  Serial.println("SYSTEM_READY");
}

void loop(void) {
  // 1. 非阻塞式重量回報 (每 2 秒執行一次)
  if (millis() - lastWeightTime > 2000) {
    if (scale.is_ready()) {
      float currentWeight = scale.get_units();
      
      // 消除微小負值跳動，確保數據乾淨
      if (currentWeight <= 0) {
        currentWeight = 0;
      }
      
      Serial.print("WEIGHT:");
      Serial.println(currentWeight, 1);
      
      lastWeightTime = millis();
    }
  }

  // 2. 接收 Python 握手協定指令
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd == "GO") {
      // 觸發馬達轉動 1 秒
      analogWrite(MOTOR_PIN, 255);
      delay(1000);
      analogWrite(MOTOR_PIN, 0);

      // 動作完成，回傳訊號給 Python
      Serial.println("DONE");
    }
  }
  
  // 保持系統迴圈穩定的小延遲
  delay(20);
}