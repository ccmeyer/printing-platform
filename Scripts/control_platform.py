from print_platform_API import *

if __name__ == '__main__':
    platform = Platform()
    platform.initiate_all()
    platform.home_dobot()
    platform.drive_platform()
    platform.disconnect_all()
