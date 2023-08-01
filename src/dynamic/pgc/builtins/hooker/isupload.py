from . import FridaHooker


if __name__ == '__main__':
    frida_hooker = FridaHooker('script.js')
    frida_hooker.hook('network')
    while frida_hooker.recorded_api is not None:
        print(frida_hooker.recorded_api)