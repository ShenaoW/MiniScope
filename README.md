# MiniDroid

MiniDroid is a framework for detecting privacy violations using hybrid analysis. It introduces a novel topological structure named MDG (MiniApp Dependency Graph) to guide dynamic testing. At the same time, MiniDroid monitors privacy practices by hooking sensitive APIs, and cross-validates with privacy policies to detect violations.

## Prerequisites

### Basics

- Ubuntu 20.04
- Rooted Android Device (Physical or Virtual)
- Local area network (Android device and Laptop could connect to each other)

### Dependencies

#### Ubuntu

1. Install requirements for `pdg_js` and `wxappUnpacker`

   ```bash
   # Make sure that node.js and npm are available
   sudo apt update && sudo apt install nodejs npm
   node --version && cd src/static/pdg_js && npm i
   cd src/static/utils/wxappUnpacker && npm i
   ```

2. Install requirements for python

   ```bash
   # Make sure that python3.7+ and pip are available
   sudo apt install python3 python3-pip
   # Install requirements
   pip3 install -r requirements.txt
   ```

3. Install Android SDK Platform-Tools 

   Android SDK is needed to run Appium and connect the android device.

   ```bash
   https://developer.android.google.cn/studio/releases/platform-tools
   ```

4. Install Appium and UIautomator2

   ```bash
   # Make sure that AndroidSDK is available
   npm i --location=global appium  # Install Appium
   appium  # make sure appium server is started
   appium driver install uiautomator2  # Install uiautomator2 driver
   ```

#### Android Device

1. Root device firstly, and **Magisk is recommended**.

   ```bash
   https://github.com/topjohnwu/Magisk
   https://topjohnwu.github.io/Magisk/install.html
   https://magiskcn.com/
   ```

2. Check the Xweb Kernel Version(Tested on 107.0.5304.141) and enable kernel debug of WeChat(Tested on 8.37).

   ```bash
   # Enter the following URL from the WeChat chat box and click
   httpbin.org/user-agent  # Check Xweb Kernel Version
   https://sites.google.com/chromium.org/driver/downloads  # Download ChromeDriver of the appropriate version into minidroid/drivers
   http://debugxweb.qq.com/?inspector=true  # Enable Xweb Kernel Debugging
   ```

3. Install Frida-server for sensitive API hooking.

   - Install with Magisk Plugin **(Recommended)**.

     ```bash
     https://github.com/ViRb3/magisk-frida
     ```

   - Install manually.

     ```bash
     # Make sure that adb is available
     https://github.com/frida/frida/releases  # Download frida-server
     adb [your-frida-server-path]./frida-server  # Start frida-server
     frida-ps -U  # Make sure that the frida-server is available now
     ```

4. Install Objection to bypass ssl pinning.

   ```bash
   # Objection: https://github.com/sensepost/objection 
   # SSL pinning: https://www.thesslstore.com/blog/an-introduction-to-pinning/
   pip3 install objection
   
   # Manually
   objection -g com.tencent.mm explore
   	android sslpinning disable
   # But code will run above automatically.
   ```

5. Install mitmproxy certificates for web packet capturing.

   ```bash
   https://docs.mitmproxy.org/stable/concepts-certificates/ # Install mitmproxy certificates
   ```

   - Android version below 8 (included)

     Device trust imported certificate. Download the certificate, and click it to install.

   - Android version above 9 (included)

     Device doesn’t trust user imported certificate. It’s needed to place the certificate in `/system/etc/security/cacerts`. If `/system` is unreadable and cannot be remounted, a customed Magisk plugin is needed.

     ```bash
     # Plugin modules: https://github.com/Magisk-Modules-Repo/energizedprotection
     git clone https://github.com/Magisk-Modules-Repo/energizedprotection.git
     
     # Modify ./module.prop as below
     id=Certs
     name=Certs
     version=***
     versionCode=***
     author=***
     description=mitmproxy and Fiddler Certs.
     
     # Place cert into ./system/etc/security/cacerts
     # Install the Magisk module.
     # Reboot, and the cert is installed.
     ```
   
   If you want to add your own packet filtering rules, add filter class to `./src/monitor/addons.py` and add the class name to `addons` variable.

### Pre-processing

#### Device connection

Connect the device with Ubuntu via Android SDK platform-tools  (remote or usb).

#### Run Appium

```bash
#! /bin/bash
export ANDROID_HOME=/usr/lib/android-sdk

echo $ANDROID_HOME
/usr/local/bin/appium
```

#### Tokens Configuration:

To obtain the current page path during dynamic testing

```bash
# Obtain page path copy permissions based on the following URL
https://kf.qq.com/faq/180725biaAn2180725VnQjYF.html
# Capture network packets(POST request)
https://mp.weixin.qq.com/cgi-bin/copywxapath?action=sendmsg_of_copywxapath
# Replace Token and Cookie in the following config
minidroid/src/dynamic/config/token/token.toml
```

To obtain the privacy policy of the MiniApp

```bash
# Access the following URL and capture network packets for WeChat PC
https://mp.weixin.qq.com/wxawap/waprivacyinfo?appid=wx210963174dd44184&action=show
# Replace the UIN, KEY, and WAP_SID2 in the following config
minidroid/src/static/pp_crawler/config.py
```

## Usage

Here're arguments:

- `-c/--config`: specify the config file path. Here's a config example.

  ```toml
  localChrome = # path to chrome driver
  appName = # name of miniapp
  appID = # appid of miniapp
  
  [capabilities]
  deviceName = # device name(remote or usb) for test 
  platformName = "Android"
  appPackage = "com.tencent.mm"
  appActivity = "com.tencent.mm.ui.LauncherUI"
  automationName = "uiautomator2"
  noReset = true
  unicodeKeyboard = true
  resetKeyboard = true
  chromedriverExecutable =  # path to chrome driver
  
  ```

- `-id/--AppId`: specify the app id of miniapp.

- `-n/--AppName`: specify the app name of miniapp.

- `-pkg/--package`: specify the package file path or folder path.

- `-pp/--privacypolicy`: specify the privacy policy file path.

- `-sa/--staticAnalyzed`:  specify the static analyzed file path.

- `-da/--dynamicAnalyzed`:  specify the static analyzed file path.

- `-ca/--combinedAnalyzed`:  specify the combined analyzed file path.

**Example:**

```bash
python3 main.py -n 遂川旅游景点 -id wx4938079035028687 -pkg data/data_runtime/wx4938079035028687 -sa data/data_runtime/wx4938079035028687/StaticAnalyzer.pkl -da data/data_runtime/wx4938079035028687/DynamicAnalyzer.pkl   
```

## License

This project is licensed under the terms of the AGPLV3 license.

* **pdg_js** is credit to [**DoubleX**](https://github.com/Aurore54F/DoubleX/)
