from print_platform_API import *

if __name__ == '__main__':
    platform = Platform()
    # platform.init_dobot()
    # platform.init_pressure()
    platform.initiate_all()
    #
    platform.home_dobot()
    # platform.change_print_position()
    platform.drive_platform()
    # platform.close_reg()
    # platform.disconnect_dobot()
    platform.disconnect_all()
