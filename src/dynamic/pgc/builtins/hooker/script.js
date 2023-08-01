// 绕过TracerPid检测
var ByPassTracerPid = function () {
    var fgetsPtr = Module.findExportByName('libc.so', 'fgets');
    var fgets = new NativeFunction(fgetsPtr, 'pointer', ['pointer', 'int', 'pointer']);
    Interceptor.replace(fgetsPtr, new NativeCallback(function (buffer, size, fp) {
        var retval = fgets(buffer, size, fp);
        var bufstr = Memory.readUtf8String(buffer);
        if (bufstr.indexOf('TracerPid:') > -1) {
            Memory.writeUtf8String(buffer, 'TracerPid:\t0');
            console.log('tracerpid replaced: ' + Memory.readUtf8String(buffer));
        }
        return retval;
    }, 'pointer', ['pointer', 'int', 'pointer']));
};

// 获取调用链
function getStackTrace() {
    var Exception = Java.use('java.lang.Exception');
    var ins = Exception.$new('Exception');
    var straces = ins.getStackTrace();
    if (undefined == straces || null == straces) {
        return;
    }
    var result = '';
    for (var i = 0; i < straces.length; i++) {
        var str = '   ' + straces[i].toString();
        result += str + '\r\n';
    }
    Exception.$dispose();
    return result;
}

function get_format_time() {
    var myDate = new Date();

    return myDate.getFullYear() + '-' + myDate.getMonth() + '-' + myDate.getDate() + ' ' + myDate.getHours() + ':' + myDate.getMinutes() + ':' + myDate.getSeconds();
}

//告警发送
function alertSend(action, messages, arg) {
    var _time = get_format_time();
    send({
        'type': 'notice',
        'time': _time,
        'action': action,
        'messages': messages,
        'arg': arg,
        'stacks': getStackTrace()
    });
}

// 增强健壮性，避免有的设备无法使用 Array.isArray 方法
if (!Array.isArray) {
    Array.isArray = function (arg) {
        return Object.prototype.toString.call(arg) === '[object Array]';
    };
}

// hook方法
function hookMethod(targetClass, targetMethod, targetArgs, action, messages) {
    try {
        var _Class = Java.use(targetClass);
    } catch (e) {
        return false;
    }

    if (targetMethod == '$init') {
        var overloadCount = _Class.$init.overloads.length;
        for (var i = 0; i < overloadCount; i++) {
            _Class.$init.overloads[i].implementation = function () {
                var temp = this.$init.apply(this, arguments);
                // 是否含有需要过滤的参数
                var argumentValues = Object.values(arguments);
                if (Array.isArray(targetArgs) && targetArgs.length > 0 && !targetArgs.every(item => argumentValues.includes(item))) {
                    return null;
                }
                var arg = '';
                for (var j = 0; j < arguments.length; j++) {
                    if (arguments[j].class == "class org.json.JSONObject") {
                        arg += arguments[j].valueOf();
                    }                }
                if (arg.length == 0)
                    arg = 'no args';
                else arg = arg.slice(0, arg.length - 1);
                alertSend(action, messages, arg);
                return temp;
            }
        }
    } else {
        try {
            var overloadCount = _Class[targetMethod].overloads.length;
        } catch (e) {
            console.log(e)
            console.log('[x] hook ' + targetMethod + ' failed, maybe it is not exits.');
            return false;
        }
        for (var i = 0; i < overloadCount; i++) {
            _Class[targetMethod].overloads[i].implementation = function () {
                var temp = this[targetMethod].apply(this, arguments);
                // 是否含有需要过滤的参数
                var argumentValues = Object.values(arguments);
                if (Array.isArray(targetArgs) && targetArgs.length > 0 && !targetArgs.every(item => argumentValues.includes(item))) {
                    return null;
                }
                var arg = '';
                for (var j = 0; j < arguments.length; j++) {
                    if (arguments[j].class == "class org.json.JSONObject") {
                        arg += arguments[j].valueOf();
                    }
                }
                if (arg.length == 0) arg = 'no args';
                else arg = arg.slice(0, arg.length - 1);
                alertSend(action, messages, arg);
                return temp;
            }
        }
    }
    return true;
}

// hook方法(去掉不存在方法）
function hook(targetClass, methodData) {
    try {
        var _Class = Java.use(targetClass);
    } catch (e) {
        return false;
    }
    var methods = _Class.class.getDeclaredMethods();
    _Class.$dispose;
    // 排查掉不存在的方法，用于各个android版本不存在方法报错问题。
    methodData.forEach(function (methodData) {
        for (var i in methods) {
            if (methods[i].toString().indexOf('.' + methodData['methodName'] + '(') != -1 || methodData['methodName'] == '$init') {
                hookMethod(targetClass, methodData['methodName'], methodData['args'], methodData['action'], methodData['messages']);
                break;
            }
        }
    });
}

// hook获取其他app信息api，排除app自身
function hookApplicationPackageManagerExceptSelf(targetMethod, action) {
    var _ApplicationPackageManager = Java.use('android.app.ApplicationPackageManager');
    try {
        try {
            var overloadCount = _ApplicationPackageManager[targetMethod].overloads.length;
        } catch (e) {
            return false;
        }
        for (var i = 0; i < overloadCount; i++) {
            _ApplicationPackageManager[targetMethod].overloads[i].implementation = function () {
                var temp = this[targetMethod].apply(this, arguments);
                var arg = '';
                for (var j = 0; j < arguments.length; j++) {
                    if (j === 0) {
                        var string_to_recv;
                        send({'type': 'app_name', 'data': arguments[j]});
                        recv(function (received_json_object) {
                            string_to_recv = received_json_object.my_data;
                        }).wait();
                    }
                    if (arguments[j].class == "class org.json.JSONObject") {
                        arg += arguments[j].valueOf();
                    }                }
                if (arg.length == 0) arg = 'no args';
                else arg = arg.slice(0, arg.length - 1);
                if (string_to_recv) {
                    alertSend(action, targetMethod + '获取的数据为: ' + temp, arg);
                }
                return temp;
            }
        }
    } catch (e) {
        console.log(e);
        return
    }


}

// 申请权限
function checkRequestPermission() {
    var action = '申请权限';

    //老项目
    hook('android.support.v4.app.ActivityCompat', [
        {'methodName': 'requestPermissions', 'action': action, 'messages': '申请具体权限看参数1'}
    ]);

    hook('androidx.core.app.ActivityCompat', [
        {'methodName': 'requestPermissions', 'action': action, 'messages': '申请具体权限见参数1'}
    ]);
}

// 获取电话相关信息
function getPhoneState() {
    var action = '获取电话相关信息';

    hook('android.telephony.TelephonyManager', [
        // Android 8.0
        {'methodName': 'getDeviceId', 'action': action, 'messages': '获取IMEI'},
        // Android 8.1、9   android 10获取不到
        {'methodName': 'getImei', 'action': action, 'messages': '获取IMEI'},

        {'methodName': 'getMeid', 'action': action, 'messages': '获取MEID'},
        {'methodName': 'getLine1Number', 'action': action, 'messages': '获取电话号码标识符'},
        {'methodName': 'getSimSerialNumber', 'action': action, 'messages': '获取IMSI/iccid'},
        {'methodName': 'getSubscriberId', 'action': action, 'messages': '获取IMSI'},
        {'methodName': 'getSimOperator', 'action': action, 'messages': '获取MCC/MNC'},
        {'methodName': 'getNetworkOperator', 'action': action, 'messages': '获取MCC/MNC'},
        {'methodName': 'getSimCountryIso', 'action': action, 'messages': '获取SIM卡国家代码'},

        {'methodName': 'getCellLocation', 'action': action, 'messages': '获取电话当前位置信息'},
        {'methodName': 'getAllCellInfo', 'action': action, 'messages': '获取电话当前位置信息'},
        {'methodName': 'requestCellInfoUpdate', 'action': action, 'messages': '获取基站信息'},
        {'methodName': 'getServiceState', 'action': action, 'messages': '获取sim卡是否可用'},
    ]);

    // 电信卡cid lac
    hook('android.telephony.cdma.CdmaCellLocation', [
        {'methodName': 'getBaseStationId', 'action': action, 'messages': '获取基站cid信息'},
        {'methodName': 'getNetworkId', 'action': action, 'messages': '获取基站lac信息'}
    ]);

    // 移动联通卡 cid/lac
    hook('android.telephony.gsm.GsmCellLocation', [
        {'methodName': 'getCid', 'action': action, 'messages': '获取基站cid信息'},
        {'methodName': 'getLac', 'action': action, 'messages': '获取基站lac信息'}
    ]);

    // 短信
    hook('android.telephony.SmsManager', [
        {'methodName': 'sendTextMessageInternal', 'action': action, 'messages': '获取短信信息-发送短信'},
        {'methodName': 'getDefault', 'action': action, 'messages': '获取短信信息-发送短信'},
        {'methodName': 'sendTextMessageWithSelfPermissions', 'action': action, 'messages': '获取短信信息-发送短信'},
        {'methodName': 'sendMultipartTextMessageInternal', 'action': action, 'messages': '获取短信信息-发送短信'},
        {'methodName': 'sendDataMessage', 'action': action, 'messages': '获取短信信息-发送短信'},
        {'methodName': 'sendDataMessageWithSelfPermissions', 'action': action, 'messages': '获取短信信息-发送短信'},
    ]);

}

// 系统信息(AndroidId/标识/content敏感信息)
function getSystemData() {
    hook()

    //获取content敏感信息
    try {
        // 通讯录内容
        var ContactsContract = Java.use('android.provider.ContactsContract');
        var contact_authority = ContactsContract.class.getDeclaredField('AUTHORITY').get('java.lang.Object');
    } catch (e) {
        console.log(e)
    }
    try {
        // 日历内容
        var CalendarContract = Java.use('android.provider.CalendarContract');
        var calendar_authority = CalendarContract.class.getDeclaredField('AUTHORITY').get('java.lang.Object');
    } catch (e) {
        console.log(e)
    }
    try {
        // 浏览器内容
        var BrowserContract = Java.use('android.provider.BrowserContract');
        var browser_authority = BrowserContract.class.getDeclaredField('AUTHORITY').get('java.lang.Object');
    } catch (e) {
        console.log(e)
    }
    try {
        // 相册内容
        var MediaStore = Java.use('android.provider.MediaStore');
        var media_authority = MediaStore.class.getDeclaredField('AUTHORITY').get('java.lang.Object');
    } catch (e) {
        console.log(e)
    }
    try {
        var ContentResolver = Java.use('android.content.ContentResolver');
        var queryLength = ContentResolver.query.overloads.length;
        for (var i = 0; i < queryLength; i++) {
            ContentResolver.query.overloads[i].implementation = function () {
                var temp = this.query.apply(this, arguments);
                if (arguments[0].toString().indexOf(contact_authority) != -1) {
                    alertSend(action, '获取手机通信录内容', '');
                } else if (arguments[0].toString().indexOf(calendar_authority) != -1) {
                    alertSend(action, '获取日历内容', '');
                } else if (arguments[0].toString().indexOf(browser_authority) != -1) {
                    alertSend(action, '获取浏览器内容', '');
                } else if (arguments[0].toString().indexOf(media_authority) != -1) {
                    alertSend(action, '获取相册内容', '');
                }
                return temp;
            }
        }
    } catch (e) {
        console.log(e);
        return
    }
}

//获取其他app信息
function getPackageManager() {
    var action = '获取其他app信息';

    hook('android.content.pm.PackageManager', [
        {'methodName': 'getInstalledPackages', 'action': action, 'messages': 'APP获取了其他app信息'},
        {'methodName': 'getInstalledApplications', 'action': action, 'messages': 'APP获取了其他app信息'}
    ]);

    hook('android.app.ApplicationPackageManager', [
        {'methodName': 'getInstalledPackages', 'action': action, 'messages': 'APP获取了其他app信息'},
        {'methodName': 'getInstalledApplications', 'action': action, 'messages': 'APP获取了其他app信息'},
        {'methodName': 'queryIntentActivities', 'action': action, 'messages': 'APP获取了其他app信息'},
    ]);

    hook('android.app.ActivityManager', [
        {'methodName': 'getRunningAppProcesses', 'action': action, 'messages': '获取了正在运行的App'},
        {'methodName': 'getRunningServiceControlPanel', 'action': action, 'messages': '获取了正在运行的服务面板'},
    ]);
    //需排除应用本身
    hookApplicationPackageManagerExceptSelf('getApplicationInfo', action);
    hookApplicationPackageManagerExceptSelf('getPackageInfoAsUser', action);
    hookApplicationPackageManagerExceptSelf('getInstallerPackageName', action);
}

// 获取位置信息
function getLocation() {
    hook('com.tencent.map.geolocation.sapp.TencentLocationManager', [
        {'methodName': 'requestSingleFreshLocation', 'action': 'wx.getLocation', 'messages': '微信小程序正尝试获取位置'},
    ]);
}

// 调用摄像头
function getCamera() {
    var action = '调用摄像头';

    hook('android.hardware.Camera', [
        {'methodName': 'open', 'action': action, 'messages': action},
    ]);

    hook('android.hardware.camera2.CameraManager', [
        {'methodName': 'openCamera', 'action': action, 'messages': action},
    ]);

    hook('androidx.camera.core.ImageCapture', [
        {'methodName': 'takePicture', 'action': action, 'messages': '调用摄像头拍照'},
    ]);

}

//获取网络信息
function getNetwork() {
    hook('jm0.a', [
        {'methodName': 'e', 'action': 'wx.request', 'messages': '微信小程序试图发送网络请求'},
    ]);

    hook('im0.a', [
        {'methodName': 'c', 'action': 'wx.downloadFile', 'messages': '微信小程序试图下载文件'},
    ]);

    hook('km0.b', [
        {'methodName': 'e', 'action': 'wx.uploadFile', 'messages': '微信小程序试图上传文件'},
    ]);
}

//获取蓝牙设备信息
function getBluetooth() {
    var action = '获取蓝牙设备信息';

    hook('android.bluetooth.BluetoothDevice', [
        {'methodName': 'getName', 'action': action, 'messages': '获取蓝牙设备名称'},
        {'methodName': 'getAddress', 'action': action, 'messages': '获取蓝牙设备mac'},
    ]);

    hook('android.bluetooth.BluetoothAdapter', [
        {'methodName': 'getName', 'action': action, 'messages': '获取蓝牙设备名称'}
    ]);
}

//读写文件
function getFileMessage() {
    var action = '文件操作';

    hook('java.io.RandomAccessFile', [
        {'methodName': '$init', 'action': action, 'messages': 'RandomAccessFile写文件'}
    ]);
    hook('java.io.File', [
        {'methodName': 'mkdirs', 'action': action, 'messages': '尝试写入sdcard创建小米市场审核可能不通过'},
        {'methodName': 'mkdir', 'action': action, 'messages': '尝试写入sdcard创建小米市场审核可能不通过'}
    ]);
}

//获取麦克风信息
function getMedia() {
    var action = '获取麦克风'

    hook('android.media.MediaRecorder', [
        {'methodName': 'start', 'action': action, 'messages': '获取麦克风'},
    ]);
    hook('android.media.AudioRecord', [
        {'methodName': 'startRecording', 'action': action, 'messages': '获取麦克风'},
    ]);
}

//获取传感器信息
function getSensor() {
    var action = '获取传感器信息'

    hook('android.hardware.SensorManager', [
        {'methodName': 'getSensorList', 'action': action, 'messages': '获取传感器信息'},
    ]);

}

function useModule(moduleList) {
    var _module = {
        'permission': [checkRequestPermission],
        'phone': [getPhoneState],
        'system': [getSystemData],
        'app': [getPackageManager],
        'location': [getLocation],
        'network': [getNetwork],
        'camera': [getCamera],
        'bluetooth': [getBluetooth],
        'file': [getFileMessage],
        'media': [getMedia],
        'sensor': [getSensor],
    };
    var _m = Object.keys(_module);
    var tmp_m = []
    if (moduleList['type'] !== 'all') {
        var input_module_data = moduleList['data'].split(',');
        for (i = 0; i < input_module_data.length; i++) {
            if (_m.indexOf(input_module_data[i]) === -1) {
                send({'type': 'noFoundModule', 'data': input_module_data[i]})
            } else {
                tmp_m.push(input_module_data[i])
            }
        }
    }
    switch (moduleList['type']) {
        case 'use':
            _m = tmp_m;
            break;
        case 'nouse':
            for (var i = 0; i < input_module_data.length; i++) {
                for (var j = 0; j < _m.length; j++) {
                    if (_m[j] == input_module_data[i]) {
                        _m.splice(j, 1);
                        j--;
                    }
                }
            }
            break;
    }
    send({'type': 'loadModule', 'data': _m})
    if (_m.length !== 0) {
        for (i = 0; i < _m.length; i++) {
            for (j = 0; j < _module[_m[i]].length; j++) {
                _module[_m[i]][j]();
            }
        }
    }
}

function main() {
    try {
        Java.perform(function () {
            console.log('[+] 隐私合规检测敏感接口开始监控');
            send({"type": "isHooked"})
            console.log('[+] 检测到安卓版本：' + Java.androidVersion);
            var moduleList;
            recv(function (received_json_object) {
                moduleList = received_json_object.use_module;
            }).wait();
            useModule(moduleList);
        });
    } catch (e) {
        console.log(e)
    }
}

// 绕过TracerPid检测 默认关闭，有必要时再自行打开
// setImmediate(ByPassTracerPid);
