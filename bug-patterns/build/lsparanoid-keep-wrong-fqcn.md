# ProGuard keep rule sai FQCN: plugin fork đổi package, rule còn ghi package gốc

## Triệu chứng
Keep rule `-keep class com.joom.paranoid.Deobfuscator**` là no-op âm thầm:
không match class nào → R8 rename `Deobfuscator` thành `Lc73;` trong
release dex (deobfuscation vẫn live một cách may mắn, không phải do keep).

## Root cause
Repo apply plugin **fork** `org.lsposed.lsparanoid` v0.6.0
(`gradle/libs.versions.toml`: group `org.lsposed.lsparanoid`), nhưng keep
rule còn ghi package của upstream gốc `com.joom.paranoid`. Class thật sinh
ra là `org.lsposed.lsparanoid.Deobfuscator$*` → rule match nothing.

## Fix
```proguard
-keep class org.lsposed.lsparanoid.Deobfuscator** { *; }
```
Pattern `**` match cả class gốc và inner class `Deobfuscator$*` theo cú
pháp ProGuard. Kèm comment NOTE giải thích package fork vs upstream.

## Check chạy được
- CI `assembleRelease` xanh.
- jadx release APK: class `Deobfuscator` giữ tên (không còn `Lc73;`);
  string obfuscation vẫn deobfuscate đúng ở runtime.
- Phòng: khi đổi/bump Gradle plugin (đặc biệt fork), grep mọi keep rule /
  reference ghi package cũ; verify bằng class thật trong dex (audit đã
  bắt bằng parser DEX), không tin comment "load-bearing" trong docs
  (AGENTS.md và release-rules.md vẫn ghi FQCN cũ — đã flag là stale).
