from print_platform_API_dup import *

if __name__ == '__main__':
    platform = Platform()
    platform.initiate_all()
    # try:
    platform.drive_platform()
    # except Exception as e:
    #     import ipdb; ipdb.set_trace()
    #     raise e
    platform.disconnect_all()
