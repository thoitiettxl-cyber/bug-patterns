# BluetoothAdapter.getAddress() MAC leak — hook thiếu getter của local adapter

## Triệu chứng
Bật spoof BT (`spoof_nearby_bt`) nhưng app vẫn đọc được MAC Bluetooth thật
qua `BluetoothAdapter.getAddress()` — SDK anti-emulator / fingerprint đọc
thẳng local MAC.

## Root cause
`NearbyBtSpoofModule` chỉ hook `getBondedDevices` (trả set rỗng) và
`BluetoothLeScanner.startScan` (fake nearby devices) — chưa bao giờ hook
getter của **local** adapter MAC. `BluetoothAdapter.getAddress()` là public
API ổn định (`public String getAddress()`, không overload, không deprecated —
AOSP `core/java/android/bluetooth/BluetoothAdapter.java`), minSdk 33 luôn
khả dụng, không cần SDK guard.

## Fix
- `getDeclaredMethod("getAddress").hookConstant(spoofedBtMac)` trong
  `install()`, mirror pattern `WifiSpoofModule.wifiReturn()`; guard
  try/catch + `Log.w` + fail open; empty profile field → skip hook hoàn
  toàn (không fallback giá trị giả — MAC BT ảnh hưởng pairing thật).
- Field mới `SPOOF_BT_MAC` vào `Profile.kt` catalogue (không thêm
  ProfileToggle — module vẫn gated bởi key `spoof_nearby_bt` hiện có).
- Populate ở MỌI kênh sinh identifier: `OneClickRandom.generate`,
  `SentinelIdentityManager.REGENERATORS`,
  `PrivacyScreen.randomizeMissingDeviceIds` /
  `randomizeAllDeviceIds` — field mới sinh ra mà kênh random không
  populate = coverage gap ngay từ đầu.

## Check chạy được
- CI `:lsmodule:test` xanh (gồm `SentinelIdentityManagerTest` 4 fields).
- Máy thật: set `SPOOF_BT_MAC` → app đọc `getAddress()` thấy MAC giả;
  one-click random → field được populate; để trống → real method chạy,
  BT hoạt động bình thường.
- Phòng: thêm identifier field mới → grep mọi nơi set field cùng nhóm
  (one-click, sentinel, editor fill/randomize) và bổ sung ngay trong
  cùng batch.
