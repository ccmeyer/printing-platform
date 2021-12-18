from print_platform_API_dup import *

if __name__ == '__main__':
    platform = Platform()
    platform.initiate_all()
    platform.drive_platform()
    platform.disconnect_all()
