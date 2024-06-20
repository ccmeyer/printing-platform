from utils import *
import json
import numpy as np
import cv2
from pynput import keyboard
from pynput.keyboard import Key
from pyautogui import press

class Robot:
    def __init__(self,sim):
        print('started Robot')

    def init_dobot(self,port):
        '''
        Establishes the connection to the Dobot and sets its movement parameters.
        It also reads in the print calibration file which includes the locations
        of the loading and tube positions.
        '''
        print('\nConnecting the Dobot...\n')

        if self.robot_type == 'Magician':
            import Dobot.DobotDllType as dType

        elif self.robot_type == 'M1':
            import DobotM1.DobotDllType as dType
            from DobotM1.DobotDllType import PTPMode

        global dType
        self.api = dType.load()

        CON_STR = {
            dType.DobotConnect.DobotConnect_NoError:  "DobotConnect_NoError",
            dType.DobotConnect.DobotConnect_NotFound: "DobotConnect_NotFound",
            dType.DobotConnect.DobotConnect_Occupied: "DobotConnect_Occupied"}
        deviceList = dType.SearchDobot(self.api)
        print(deviceList)

        if port in deviceList:
            print('Default Dobot COM port found')
            target_port = self.default_settings['Dobot_port']
        else:
            print(f'Unable to find default Dobot COM port {port}')
            target_port = select_options(deviceList)

        print("Connecting... ", target_port)
        state = dType.ConnectDobot(self.api,  target_port, 115200)[0]
        print("Connect status:",CON_STR[state])

        if (state == dType.DobotConnect.DobotConnect_NoError):
            dType.SetQueuedCmdStopExec(self.api)
            dType.SetQueuedCmdClear(self.api)
        else:
            print('failed')
            return

        dType.SetPTPCommonParams(self.api, 20, 20, isQueued = 1)
        if not self.sim:
            dobot_coords = dType.GetPose(self.api)
            self.current_coords = {'x':dobot_coords[0],'y':dobot_coords[1],'z':dobot_coords[2]}
            print('current_coords:', self.current_coords)
            # self.current_coords = self.calibration_data['loading']
        return

    def disconnect_dobot(self):
        if not self.sim:
            self.deactivate_gripper()
            dType.SetQueuedCmdStopExec(self.api)
            dType.DisconnectDobot(self.api)
        print('Disconnected Dobot')
        return

    def get_dobot_calibrations(self):
        # Extract all calibration data
        try:
            self.calibration_file_path = self.get_file_path('Calibrations/print_calibrations_{}_{}.json'.format(self.default_settings['robot_type'],self.mode),base=True)
            with open(self.calibration_file_path) as json_file:
                self.calibration_data =  json.load(json_file)
            print('Loaded printing calibration: {}_{}'.format(self.default_settings['robot_type'],self.mode))

        except:
            all_calibrations = self.get_all_paths('Calibrations/*print*',base=True)
            print('Possible printing calibrations:')

            target = select_options(all_calibrations,trim=True)
            print('Chosen plate: ',target)
            self.calibration_file_path = target

            with open(self.calibration_file_path) as json_file:
                self.calibration_data =  json.load(json_file)
        if self.sim:
            self.current_coords = self.calibration_data['loading']
        self.get_plate_data()
        return

    def run_cmd(self):
        '''
        Executes the dobot's queued commands
        '''
        lastQueuedIndex = dType.SetWAITCmd(self.api, 0.1, isQueued=1)[0]
        dType.SetQueuedCmdStartExec(self.api)
        #Wait for Executing Last Command
        while lastQueuedIndex > dType.GetQueuedCmdCurrentIndex(self.api)[0]:
            dType.dSleep(10)

        #Stop to Execute Command Queued
        dType.SetQueuedCmdClear(self.api)
        return

    def home_dobot(self):
        '''
        Initially resets the Dobot's position and then initiates the homing
        protocol. Reseting the position ensures that the arm is not extended
        when rotating
        '''
        if not self.ask_yes_no(message='Home Dobot? (y/n)'):
            return
        print("Homing...")
        self.reset_dobot_position()
        if not self.sim:
            if self.robot_type == 'Magician':
                last_index = dType.SetHOMECmd(self.api, temp = 0, isQueued = 1)
        self.run_cmd()
        self.location = 'home'
        return

    def move_dobot(self,x,y,z,verbose=True,check=False):
        '''
        Takes a set of XYZ coordinates and moves the Dobot to that location
        '''
        if verbose:
            print('Dobot moving...',end='')
        if not self.sim:
            last_index = dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVJXYZMode, x,y,z,0, isQueued = 1)
            self.run_cmd()
        self.current_coords = {'x':float(x),'y':float(y),'z':float(z)}
        if verbose:
            print('Current position: x={}\ty={}\tz={}'.format(round(x,2),round(y,2),round(z,2)))
        return

    def activate_gripper(self):
        if not self.sim:
            if self.robot_type == 'M1':
                dType.SetIODO(self.api, 17, 1, 1)
                dType.SetIODO(self.api, 18, 1, 1)
                self.run_cmd()
            elif self.robot_type == 'Magician':
                last_index = dType.SetEndEffectorGripper(self.api,True,False,isQueued=1)
        print('Activated gripper')
        return

    def deactivate_gripper(self):
        if not self.sim:
            if self.robot_type == 'M1':
                dType.SetIODO(self.api, 17, 0, 1)
                dType.SetIODO(self.api, 18, 1, 1)
                self.run_cmd()
            elif self.robot_type == 'Magician':
                last_index = dType.SetEndEffectorGripper(self.api,False,False,isQueued=1)
        print('Deactivated gripper')
        return

    def open_gripper(self):
        if not self.sim:
            if self.robot_type == 'M1':
                dType.SetIODO(self.api, 17, 1, 1)
                dType.SetIODO(self.api, 18, 0, 1)
                self.run_cmd()
            elif self.robot_type == 'Magician':
                last_index = dType.SetEndEffectorGripper(self.api,True,False,isQueued=1)
        print('- Gripper open')
        return

    def close_gripper(self):
        if not self.sim:
            if self.robot_type == 'M1':
                dType.SetIODO(self.api, 17, 0, 1)
                dType.SetIODO(self.api, 18, 0, 1)
                self.run_cmd()
            elif self.robot_type == 'Magician':
                last_index = dType.SetEndEffectorGripper(self.api,True,True,isQueued=1)
        print('- Gripper closed')
        return

    def load_gripper(self):
        '''
        Initiates a protocol to open and close the gripper to make exchanging
        printer heads easier
        '''
        if not self.ask_yes_no(message='Load gripper? (y/n)'): return
        input('Press enter to open gripper')
        self.open_gripper()
        input('Press enter to close gripper')
        self.close_gripper()
        return

    def dobot_manual_drive(self):
        '''
        Initiates the manual drive protocol to control the movement of the
        Dobot using the keyboard. Directs movement in the XYZ
        directions by a defined step size that can be changed to allow for
        coarse or fine grain movement
        '''
        section_break()
        print("starting manual dobot control")
        self.keyboard_config = 'Manual dobot control'
        self.update_monitor()

        x = self.current_coords['x']
        y = self.current_coords['y']
        z = self.current_coords['z']
        possible_steps = [0.1,0.5,1,5,10,20]
        step_num = (len(possible_steps)*10) + 1
        step = possible_steps[abs(step_num) % len(possible_steps)]
        while True:
            key = self.get_current_key()
            if key == Key.up:
                x -= step
            elif key == Key.down:
                x += step
            elif key == Key.left:
                y -= step
            elif key == Key.right:
                y += step
            elif key == "'":
                z += step
            elif key == "/":
                z -= step
            elif key == ';':
                step_num = step_num + 1
                step = possible_steps[abs(step_num) % len(possible_steps)]
                print('changed to {}'.format(step))
            elif key == '.':
                step_num = step_num - 1
                step = possible_steps[abs(step_num) % len(possible_steps)]
                print('changed to {}'.format(step))
            elif key == "q":
                if self.ask_yes_no(message='Quit (y/n)'):
                    print('Quitting...')
                    section_break()
                    return
                else:
                    print("Didn't quit")
            elif key == Key.esc:
                continue
            else:
                print(f'{key} is not a valid input')
            self.move_dobot(x,y,z)
        return

    def gen_trans_matrix(self):
        '''
        Performs a 4-point transformation of the coordinate plane using the
        experimentally derived plate corners. This takes the dobot coordinates
        and finds the matrix required to convert them into the coordinate plane
        that matches the defined geometry of the plate. This matrix can then be
        reversed and used to take the positions where wells should be and
        convert them into the corresponding dobot coordinates.

        This transformation accounts for the deviations in the Dobot coordinate
        system but only applies to the X and Y dimensions.
        '''
        self.trans_matrix = cv2.getPerspectiveTransform(self.corners, self.plate_dimensions)
        self.inv_trans_matrix = np.linalg.pinv(self.trans_matrix)
        return

    def get_coords(self,coords):
        '''
        Converts the coordinates stored in a dictionary to a numpy array
        '''
        return np.array(list(coords.values()))

    def get_plate_data(self):
        '''
        Extracts the metadata about a given well plate and stores it. It also
        generates the transformation matrix needed to correct the deviations
        in the Dobot positioning. Also accounts for deviations in the Z dimension
        '''
        try:
            self.plate_file_path = self.get_file_path('Calibrations/{}_{}_{}.json'.format(self.default_settings['plate_type'],self.default_settings['robot_type'],self.mode),base=True)
            with open(self.plate_file_path) as json_file:
                self.plate_data =  json.load(json_file)
            print('Loaded plate calibration: {}_{}_{}'.format(self.default_settings['plate_type'],self.default_settings['robot_type'],self.mode))
        except:
            print('Unable to find file based on defaults:')
            all_calibrations = self.get_all_paths('Calibrations/*well*',base=True)
            target = select_options(all_calibrations,message='Chose from the possible calibrations:',trim=True)

            print('Chosen plate: ',target)
            self.plate_file_path = target
            with open(self.plate_file_path) as json_file:
                self.plate_data =  json.load(json_file)
        self.plate_name = self.plate_data['plate_name']
        self.spacing = self.plate_data['well_spacing']
        self.max_rows = self.plate_data['rows'] - 1
        self.max_columns = self.plate_data['columns'] - 1

        self.top_left = self.plate_data['top_left']
        self.top_right = self.plate_data['top_right']
        self.bottom_right = self.plate_data['bottom_right']
        self.bottom_left = self.plate_data['bottom_left']

        self.corners = np.array([self.get_coords(self.top_left)[:2],self.get_coords(self.top_right)[:2],self.get_coords(self.bottom_right)[:2],self.get_coords(self.bottom_left)[:2]], dtype = "float32")
        self.plate_width = self.max_columns * self.spacing
        self.plate_depth = self.max_rows * self.spacing

        self.plate_dimensions = np.array([
            [0, 0],
            [0, self.plate_width],
            [self.plate_depth,self.plate_width],
            [self.plate_depth,0]], dtype = "float32")

        self.gen_trans_matrix()

        self.row_z_step = (self.bottom_left['z'] - self.top_left['z']) / (self.max_rows)
        self.col_z_step =  (self.top_right['z'] - self.top_left['z']) / (self.max_columns)

        # self.current_coords = self.top_left
        return

    def write_plate_data(self):
        '''
        Takes all of the current plate data and updates the metadata file
        '''
        if not self.ask_yes_no(message="Store print position? (y/n)"): return
        self.plate_data['top_left'] = self.top_left
        self.plate_data['top_right'] = self.top_right
        self.plate_data['bottom_right'] = self.bottom_right
        self.plate_data['bottom_left'] = self.bottom_left

        print(self.plate_data)

        if not self.ask_yes_no(message="Write print position to file? (y/n)"): return
        with open(self.plate_file_path, 'w') as outfile:
            json.dump(self.plate_data, outfile)
        print("Plate data saved")
        self.write_printing_calibrations(ask=False)

        return

    def write_printing_calibrations(self,ask=True):
        '''
        Updates the print calibrations json file
        '''
        if ask:
            if not self.ask_yes_no(message="Write print position to file? (y/n)"): return

        with open(self.calibration_file_path, 'w') as outfile:
            json.dump(self.calibration_data, outfile)
        print("Printing calibrations saved")

    def correct_xy_coords(self,x,y):
        '''
        Uses the transformation matrix to correct the XY coordinates
        '''
        target = np.array([[x,y]], dtype = "float32")
        target_transformed = cv2.perspectiveTransform(np.array(target[None,:,:]), self.inv_trans_matrix)
        return target_transformed[0][0]

    def get_well_coords(self,row,column):
        '''
        Uses the well indices to determine the dobot coordinates of the well
        '''
        x,y = self.correct_xy_coords(row*self.spacing,column*self.spacing)
        z = self.top_left['z'] + (row * self.row_z_step) + (column * self.col_z_step)
        return {'x':x, 'y':y, 'z':z}
