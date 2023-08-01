# MiniDroid

MiniDroid is a framework for detecting privacy violations using hybrid analysis. It introduces a novel topological structure named MDG (MiniApp Dependency Graph) to guide dynamic testing. At the same time, MiniDroid monitors privacy practices by hooking sensitive APIs, and cross-validates with privacy policies to detect violations.

## Prerequisites

### Basics

- Ubuntu 20.04
- Android Virtual Device (Android8.1, rooted)

### Dependencies

**For Ubuntu:**

Install requirements for `pdg_js` and `wxappUnpacker`

```bash
# Make sure that node.js and npm are available
node --version && cd src/static/pdg_js && npm i  #
cd src/static/utils/wxappUnpacker && npm i
```

Install requirements for python

```bash
# Install requirements
pip install -r requirements.txt
```

**For Android Virtual Device:**

Install Appium and UIautomator2

```bash
# Make sure that AndroidSDK is available
npm i --location=global appium  # Install Appium
appium  # make sure appium server is started
appium driver install uiautomator2  # Install uiautomator2 driver
```

Check the Xweb Kernel Version and enable kernel debug of WeChat (Tested on 107.0.5304.141)

```bash
# Enter the following URL from the WeChat chat box and click
httpbin.org/user-agent  # Check Xweb Kernel Version
https://sites.google.com/chromium.org/driver/downloads  # Download ChromeDriver of the appropriate version into minidroid/drivers
http://debugxweb.qq.com/?inspector=true  # Enable Xweb Kernel Debugging
```

Install Frida-server for sensitive API hooking

```bash
# Make sure that adb is available
https://github.com/frida/frida/releases  # Download frida-server
adb [your-frida-server-path]./frida-server  # Start frida-server
frida-ps -U  # Make sure that the frida-server is available now
```

Install mitmproxy certificates and objection for web packet capture

```bash
https://github.com/sensepost/objection # Install objection to bypass ssl pinning
https://docs.mitmproxy.org/stable/concepts-certificates/ # Install mitmproxy certificates

# If Android version is 9, Magisk is recommended. You can import certificate via Magisk plugin.
```

### Pre-processing

**Tokens Configuration:**

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

```bash
python main.py -n 遂川旅游景点 -id wx4938079035028687 -pkg data/data_runtime/wx4938079035028687 -sa data/data_runtime/wx4938079035028687/StaticAnalyzer.pkl -da data/data_runtime/wx4938079035028687/DynamicAnalyzer.pkl   
```

## License

This project is licensed under the terms of the AGPLV3 license.

* **pdg_js** is credit to [**DoubleX**](https://github.com/Aurore54F/DoubleX/)
