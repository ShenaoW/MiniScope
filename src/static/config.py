import os
import sys

PROJECT_PATH = os.path.dirname(os.path.abspath('__file__'))
SAVE_PATH_UTG = os.path.dirname(os.path.abspath('__file__'))+'/result/utg'
SAVE_PATH_FCG = os.path.dirname(os.path.abspath('__file__'))+'/result/fcg'
UNPACK_COMMAND = 'node ' + PROJECT_PATH + os.sep + 'src/utils/wxappUnpacker/wuWxapkg.js {}'

LIFECYCLE_CALLBACKS = [
    'onLaunch',
    'onShow',
    'onHide',
    'onError',
    'onLoad',
    'onReady',
    'onUnload',
    'onRouteDone'
]

EVENT_HANDLER_CALLBACKS = [
    'onError',
    'onPageNotFound',
    'onUnhandledRejection',
    'onThemeChange',
    'onPullDownRefresh',
    'onReachBottom',
    'onShareAppMessage',
    'onShareTimeline',
    'onAddToFavorites',
    'onPageScroll',
    'onResize',
    'onTabItemTap',
    'onSaveExitState'
]

SENSITIVE_API = {
    'wx.getUserInfo': '收集你的微信昵称、头像',
    'wx.getUserProfile': '收集你的微信昵称、头像',
    # '<button open-type="userInfo">': '收集你的微信昵称、头像',
    'wx.getLocation': '收集你的位置信息',
    'wx.getFuzzyLocation': '收集你的位置信息',
    'wx.onLocationChange': '收集你的位置信息',
    'wx.startLocationUpdate': '收集你的位置信息',
    'wx.startLocationUpdateBackground': '收集你的位置信息',
    'wx.choosePoi': '收集你的位置信息',
    'wx.chooseLocation': '收集你的位置信息',
    'wx.chooseAddress': '收集你的地址',
    'wx.chooseInvoiceTitle': '收集你的发票信息',
    'wx.chooseInvoice': '收集你的发票信息',
    'wx.getWeRunData': '收集你的微信运动步数',
    # "<button open-type='getPhoneNumber'>": '收集你的手机号',
    'wx.chooseLicensePlate': '收集你的车牌号',
    'wx.chooseImage': '收集你选中的照片或视频信息',
    'wx.chooseMedia': '收集你选中的照片或视频信息',
    'wx.chooseVideo': '收集你选中的照片或视频信息',
    'wx.chooseMessageFile': '收集你选中的文件',
    'wx.startRecord': '访问你的麦克风',
    'wx.getRecorderManager': '访问你的麦克风',
    'wx.joinVoIPChat': '访问你的麦克风',
    'wx.createCameraContext': '访问你的摄像头',
    'wx.createVKSession': '访问你的摄像头',
    'wx.createLivePusherContext': '访问你的摄像头',
    # '<camera>': '访问你的摄像头',
    # '<live-pusher>': '访问你的摄像头',
    # '<voip-room>': '访问你的摄像头',
    'wx.openBluetoothAdapter': '访问你的蓝牙',
    'wx.createBLEPeripheralServer': '访问你的蓝牙',
    'wx.saveImageToPhotosAlbum': '使用你的相册（仅写入）权限',
    'wx.saveVideoToPhotosAlbum': '使用你的相册（仅写入）权限',
    'wx.addPhoneContact': '使用你的通讯录（仅写入）权限',
    'wx.addPhoneRepeatCalendar': '使用你的日历（仅写入）权限',
    'wx.addPhoneCalendar': '使用你的日历（仅写入）权限'
}

SINK_API = [
    'wx.request',
    'wx.uploadFile',
    'wx.connectSocket',
    'wx.createTCPSocket',
    'wx.createUDPSocket',
    'wx.setStorageSync',
    'wx.setStorage'
]

ROUTE_API = [
    'wx.switchTab',
    'wx.reLaunch',
    'wx.redirectTo',
    'wx.navigateTo',
    'wx.navigateToSync',
    'wx.navigateBack'
]

NAVIGATE_API = [
    'wx.navigateToMiniProgram',
    'wx.navigateBackMiniProgram',
    'wx.exitMiniProgram'
]

BINDING_PREFIX = [
    'bind', 'bind:', 'capture-bind:',
    'catch', 'catch:', 'capture-catch:', 
    'mut-bind:'
]

BUBBLING_EVENTS = [
    'tap', 'longpress', 'longtap',
    'transitionend', 'animationstart', 'animationiteration', 'animationend', 
    'touchstart', 'touchmove', 'touchcancel', 'touchend', 'touchforcechange'
]

BINDING_EVENTS = []
# Add all Bubbling Events with each prefix
for prefix in BINDING_PREFIX:
    for event in BUBBLING_EVENTS:
        BINDING_EVENTS.append(prefix + event)

BINDING_EVENTS += [
    # Non-bubbling Events in Specific Compenonts

    # <button>
    'bindgetuserinfo', 
    'bindgetphonenumber',
    'bindchooseavatar',
    'bindopensetting',
    'bindlaunchapp', 
    'bindsubmit', 

    # <scroll-view>
    'binddragstart', 
    'binddragging', 
    'binddragend', 
    'bindscrolltoupper', 
    'bindscrolltolower', 
    'bindscroll', 
    'bindrefresherpulling', 
    'bindrefresherrefresh', 
    'bindrefresherrestore', 
    'bindrefresherabort',

    # <page-container>
    'bind:beforeenter', 
    'bind:enter', 
    'bind:afterenter', 
    'bind:beforeleave', 
    'bind:leave', 
    'bind:afterleave', 
    'bind:clickoverlay',

    # <movable-view>
    'bindscale',

    # <cover-image>
    'bindload',
    'binderror',

    # <checkbox-group>
    'bindchange',

    # <editor>
    'bindready', 
    'bindfocus', 
    'bindblur', 
    'bindinput', 
    'bindstatuschange',

    # <form>
    'bindreset',

    # <input>
    'bindconfirm',
    'bindkeyboardheightchange',
    'bindnicknamereview',

    # <picker>
    'bindcancel',
    'bindcolumnchange'  # mode = multiSelector

    # <picker-view>
    'bindpickstart', 
    'bindpickend',

    # <slider>
    'bindchanging',

    # <textarea>
    'bindlinechange',

    # <progress>
    'bindactiveend',

    # <swiper>
    'bindtransition',
    'bindanimationfinish',

    # <navigator>/<functional-page-navigator>
    'bindsuccess',
    'bindfail',
    'bindcomplete',
    'bindcancel',

    # <audio>
    'bindplay', 
    'bindpause', 
    'bindtimeupdate', 
    'bindended',

    # <camera>
    'bindstop', 
    'bindinitdone', 
    'bindscancode',

    # <video>
    'bindfullscreenchange', 
    'bindwaiting', 
    'bindprogress', 
    'bindloadedmetadata', 
    'bindcontrolstoggle', 
    'bindenterpictureinpicture', 
    'bindleavepictureinpicture', 
    'bindseekcomplete',

    # <live-player>
    'bindstatechange', 
    'bindnetstatus', 
    'bindaudiovolumenotify', 

    # <map>
    'bindmarkertap', 
    'bindlabeltap', 
    'bindcontroltap', 
    'bindcallouttap', 
    'bindupdated', 
    'bindregionchange', 
    'bindpoitap', 
    'bindanchorpointtap',
]