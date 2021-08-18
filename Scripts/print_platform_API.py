from Precigenome.PGMFC import PGMFC

import time
import serial
import sys
import msvcrt
import json
import numpy as np
import pandas as pd
import math
import cv2
import glob
import os
from pynput import keyboard
from pynput.keyboard import Key
import datetime

import tkinter as tk
from tkinter import ttk
import threading


def SetParam_CtrlSeq(feq,pw,repw,pc):  # frequency, pulsewidth and pulsecount
    '''
    Packages the printing information for transfer to the Arduino to open and
    close the valves as instructed. The Arduino should be loaded with the program
    arduino_valve_control.ino
    '''
    single_Ctrl = [255,255]
    single_Ctrl.append(feq)
    single_Ctrl.append(pw%256)
    single_Ctrl.append(pw//256)
    single_Ctrl.append(repw%256)
    single_Ctrl.append(repw//256)
    single_Ctrl.append(pc)
    temp = bytes(single_Ctrl)
    return temp

def Switch_CtrlSeq(state):
    '''
    Signals to the Arduino that the printing command is complete
    '''
    single_Ctrl=[]
    if state == 'close':
        single_Ctrl = [255,255,239,239]
    elif state == 'print':
        single_Ctrl = [255,255,254,254]
    elif state == 'refuel':
        single_Ctrl = [255,255,237,237]
    elif state == 'pulse':
        single_Ctrl = [255,255,235,235]
    return bytes(single_Ctrl)

def get_coords(coords):
    '''
    Converts the coordinates stored in a dictionary to a numpy array
    '''
    return np.array(list(coords.values()))

def section_break():
    print("\n==================================================================\n")
    return

def print_title(title):
    section_break()
    print(title)
    section_break()
    return

def select_options(lst,message='Select one of the options:', trim=False):
    if len(lst) == 0:
        print('No options to select')
        return
    if trim:
        simple_paths = []
        for l in lst:
            if l.replace('\\','/').split('/')[-1] == '':
                simple_paths.append(l.replace('\\','/').split('/')[-2])
            else:
                simple_paths.append(l.replace('\\','/').split('/')[-1])
    else:
        simple_paths = lst
    for index,opt in enumerate(simple_paths):
        print(index,opt)
    enteredStr = input(message)
    while not enteredStr.isnumeric() or int(enteredStr) >= len(lst) or int(enteredStr) < 0:
        enteredStr = input("The entered command is invalid. Please enter a valid index: ")
    print('Option selected: ',lst[int(enteredStr)],'\n')
    return lst[int(enteredStr)]

def ask_for_number(message='Enter number: '):
    try:
        return float(input(message))

    except:
        print('Not a valid input')
        return ask_for_number()


class Monitor(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()

    def callback(self):
        self.root.quit()

    def run(self):
        self.root = tk.Tk()
        self.root.geometry("300x300")
        self.root.title("Status window")
        self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root.resizable(0, 0)

        # configure the grid
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)

        self.label_0 = tk.StringVar()
        self.label_0.set('Mode')
        self.l_0 = ttk.Label(self.root, textvariable=self.label_0)
        self.l_0.grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)

        self.info_0 = tk.StringVar()
        self.info_0.set('---')
        self.i_0 = ttk.Label(self.root, textvariable=self.info_0)
        self.i_0.grid(column=1, row=0, sticky=tk.W, padx=5, pady=5)

        self.label_1 = tk.StringVar()
        self.label_1.set('Current Row')
        self.l_l = ttk.Label(self.root, textvariable=self.label_1)
        self.l_l.grid(column=0, row=1, sticky=tk.W, padx=5, pady=5)

        self.info_1 = tk.StringVar()
        self.info_1.set('---')
        self.i_1 = ttk.Label(self.root, textvariable=self.info_1)
        self.i_1.grid(column=1, row=1, sticky=tk.W, padx=5, pady=5)

        self.label_2 = tk.StringVar()
        self.label_2.set('Current Column')
        self.l_2 = ttk.Label(self.root, textvariable=self.label_2)
        self.l_2.grid(column=0, row=2, sticky=tk.W, padx=5, pady=5)

        self.info_2 = tk.StringVar()
        self.info_2.set('---')
        self.i_2 = ttk.Label(self.root, textvariable=self.info_2)
        self.i_2.grid(column=1, row=2, sticky=tk.W, padx=5, pady=5)

        self.label_3 = tk.StringVar()
        self.label_3.set('Current keyboard function')
        self.l_3 = ttk.Label(self.root, textvariable=self.label_3)
        self.l_3.grid(column=0, row=3, sticky=tk.W, padx=5, pady=5)

        self.info_3 = tk.StringVar()
        self.info_3.set('---')
        self.i_3 = ttk.Label(self.root, textvariable=self.info_3)
        self.i_3.grid(column=1, row=3, sticky=tk.W, padx=5, pady=5)

        self.root.mainloop()

    def end_monitor(self):
        print('Close the monitor...')

##### MAIN CLASS DEFINITION  ######

class Platform():
    '''
    The platform class includes all the methods required to control the Dobot
    robotic arm, the Arduino and the Precigenome pressure regulator
    '''
    def __init__(self):
        print('Created platform instance')
        self.start_tracker()
        self.current_key = False
        self.sim = self.ask_yes_no(message='Run Simulation? (y/n)')
        # self.sim = False
        self.monitor = Monitor()
        self.keyboard_config = 'empty'
        self.location = 'unknown'
        self.current_row = 0
        self.current_column = 0
        self.read_defaults()
        return

    def update_monitor(self):
        self.monitor.info_0.set(str(self.mode))
        self.monitor.info_1.set(str(self.current_row))
        self.monitor.info_2.set(str(self.current_column))
        self.monitor.info_3.set(str(self.keyboard_config))


    def on_press(self,key):
        self.shift = False
        self.current_key = key
        self.time_stamp = datetime.datetime.now().timestamp()
        if key == keyboard.Key.esc:
            self.pause = True
        if key == Key.shift or key == Key.shift_r:
            self.shift = True

    def start_tracker(self):
        print('starting traker')
        self.pause = False
        self.listener = keyboard.Listener(
            on_press=self.on_press)
        self.listener.start()
        self.time_stamp = datetime.datetime.now().timestamp()
        return

    def stop_monitor(self):
        self.listener.stop()
        return

    def get_current_key(self):
        while True:
            if self.current_key and datetime.datetime.now().timestamp() - self.time_stamp < 0.5:
                if self.current_key not in [Key.shift,Key.shift_r,Key.enter]:
                    try:
                        output = self.current_key.char
                    except:
                        output = self.current_key
                    self.current_key = False
                    return output
            time.sleep(0.01)

    def ask_yes_no(self,message='Choose yes (y) or no (n)'):
        print(message)
        while True:
            key = self.get_current_key()
            if type(key) != type('string'):
                continue
            if key == 'y':
                return True
            elif key == 'n':
                return False
            else:
                print(f'{key} is not a valid input')

    def ask_yes_no_quit(self,message='Choose yes (y), no (n), or quit (q)'):
        '''
        Simple function to double check that the operator wants to commit to an action
        '''
        print(message)
        while True:
            key = self.get_current_key()
            if type(key) != type('string'):
                continue
            if key == 'y':
                return 'yes'
            elif key == 'n':
                return 'no'
            elif key == 'q':
                return 'quit'
            else:
                print(f'{key} is not a valid input')

    def read_defaults(self):
        with open('./default_settings.json') as json_file:
            self.default_settings =  json.load(json_file)
        print('Read the default_settings.json file')
        self.base = self.default_settings['base_path']
        self.robot_type = self.default_settings['robot_type']

        self.possible_dispensers = list(self.default_settings['dispenser_types'].keys())
        print('Possible modes:',self.possible_dispensers)

        self.mode = None
        self.select_mode(mode_name=self.default_settings['default_dispenser'])
        return

    def select_mode(self,mode_name=False):
        if not mode_name:
            current_index = self.possible_dispensers.index(self.mode)
            new_index = (current_index + 1) % len(self.possible_dispensers)
            print(self.possible_dispensers[new_index])

            self.load_dispenser_defaults(self.possible_dispensers[new_index])
            return
        elif self.mode == mode_name:
            print('Already in the selected mode')
            self.load_dispenser_defaults(mode_name)
            return
        else:
            if not mode_name in self.possible_dispensers:
                print('Not an available mode')
                return
            else:
                self.load_dispenser_defaults(mode_name)
                return

    def load_dispenser_defaults(self,mode):
        print('Loading mode:',mode)
        self.height = self.default_settings['dispenser_types'][mode]['height']
        self.refuel_width = self.default_settings['dispenser_types'][mode]['refuel_width']
        self.pulse_width = self.default_settings['dispenser_types'][mode]['pulse_width']
        self.refuel_pressure = self.default_settings['dispenser_types'][mode]['refuel_pressure']
        self.pulse_pressure = self.default_settings['dispenser_types'][mode]['pulse_pressure']
        self.test_droplet_count = self.default_settings['dispenser_types'][mode]['test_droplet_count']
        self.frequency = self.default_settings['dispenser_types'][mode]['frequency']
        self.max_volume =  self.default_settings['dispenser_types'][mode]['max_volume']
        self.min_volume =  self.default_settings['dispenser_types'][mode]['min_volume']
        self.current_volume = 0
        self.calibrated = False
        self.tracking_volume = False
        self.mode = mode
        self.update_monitor()
        self.get_dobot_calibrations()
        return

    def get_file_path(self,path,base=False):
        if base:
            path = ''.join([self.base,path])
        paths = glob.glob(path)
        if len(paths) == 1:
            return paths[0]
        elif len(paths) == 0:
            print('Path: {} was not found'.format(path))
            return
        else:
            print('Found multiple paths')
            return select_options(paths,trim=True)

    def get_all_paths(self,path,base=False):
        if base:
            path = ''.join([self.base,path])
        paths = glob.glob(path)
        if len(paths) == 1:
            return paths[0]
        elif len(paths) == 0:
            print('Path: {} was not found'.format(path))
            return
        else:
            return paths

    def initiate_all(self):
        section_break()
        print('Initializing all components')
        if not self.sim:
            self.init_pressure()
            self.init_dobot(self.default_settings['Dobot_port'])
            self.init_ard(self.default_settings['Arduino_port'])
        print('All components are connected')
        section_break()
        return

    def disconnect_all(self):
        section_break()
        print('Disconnecting all components...')
        if not self.sim:
            self.disconnect_dobot()
            self.close_ard()
            self.pressure_off()
            self.close_reg()
        print('All components are disconnected')
        section_break()
        return

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

    def reset_dobot_position(self):
        '''
        Moves the Dobot to a location where its range is limited to avoid
        the arm making contact during homing
        '''
        if not self.ask_yes_no(message="Reset Dobot position? (y/n)"):
            return
        self.move_dobot(self.loading_position['x'],self.loading_position['y'],self.loading_position['z'])
        self.move_dobot(self.home_position['x'],self.home_position['y'],self.home_position['z'])
        self.location = 'home'
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

        self.corners = np.array([get_coords(self.top_left)[:2],get_coords(self.top_right)[:2],get_coords(self.bottom_right)[:2],get_coords(self.bottom_left)[:2]], dtype = "float32")
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

    def modify_coords(self,coords_1,coords_2):
        coord_diffs = {'x':(coords_1['x'] - coords_2['x']),'y':(coords_1s['y'] - coords_2['y']),'z':(coords_1s['z'] - coords_2['z'])}


    def change_print_position(self):
        '''
        Initiates a protocol to modify the expected well locations of a given
        plate. Moves from corner to corner allowing the operator to manually
        drive the dobot to correct any deviations. Once all the points are
        corrected, the new positions are stored in the plate metadata file.
        '''
        if not self.ask_yes_no(message="Change print position? (y/n)"): return
        self.move_to_location(location='print',check=True)
        self.dobot_manual_drive()
        coord_diffs = {'x':(self.current_coords['x'] - self.top_left['x']),'y':(self.current_coords['y'] - self.top_left['y']),'z':(self.current_coords['z'] - self.top_left['z'])}
        print(coord_diffs)
        self.top_left = self.current_coords
        self.calibration_data['print'] = self.current_coords
        self.write_printing_calibrations()

        self.move_dobot(self.top_right['x'], self.top_right['y'], self.top_right['z'],check=True)
        self.dobot_manual_drive()
        coord_diffs = {'x':(self.current_coords['x'] - self.top_right['x']),'y':(self.current_coords['y'] - self.top_right['y']),'z':(self.current_coords['z'] - self.top_right['z'])}
        print(coord_diffs)
        self.top_right = self.current_coords

        self.move_dobot(self.bottom_right['x'], self.bottom_right['y'], self.bottom_right['z'],check=True)
        self.dobot_manual_drive()
        coord_diffs = {'x':(self.current_coords['x'] - self.bottom_right['x']),'y':(self.current_coords['y'] - self.bottom_right['y']),'z':(self.current_coords['z'] - self.bottom_right['z'])}
        print(coord_diffs)
        self.bottom_right = self.current_coords

        self.move_dobot(self.bottom_left['x'], self.bottom_left['y'], self.bottom_left['z'],check=True)
        self.dobot_manual_drive()
        coord_diffs = {'x':(self.current_coords['x'] - self.bottom_left['x']),'y':(self.current_coords['y'] - self.bottom_left['y']),'z':(self.current_coords['z'] - self.bottom_left['z'])}
        print(coord_diffs)
        self.bottom_left = self.current_coords

        self.gen_trans_matrix()

        self.row_z_step = (self.bottom_left['z'] - self.top_left['z']) / (self.max_rows )
        self.col_z_step =  (self.top_right['z'] - self.top_left['z']) / (self.max_columns)

        self.write_plate_data()
        return

    def change_position(self,location=False):
        if not location:
            location = select_options(list(self.calibration_data.keys()))
        if not location in self.calibration_data.keys():
            print('{} not present in calibration data')
            return
        self.move_to_location(location=location,check=True)
        self.dobot_manual_drive()
        self.calibration_data[location] = self.current_coords
        self.write_printing_calibrations()
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

    def write_printing_calibrations(self):
        '''
        Updates the print calibrations json file
        '''
        if not self.ask_yes_no(message="Write print position to file? (y/n)"): return
        with open(self.calibration_file_path, 'w') as outfile:
            json.dump(self.calibration_data, outfile)
        print("Printing calibrations saved")

    def move_to_location(self,location=False,height='exact',direct=False,check=False):
        print('Current',self.location)
        if not location:
            location = select_options(list(self.calibration_data.keys()))
        if height != 'exact':
            location_name = '_'.join([height,location])
        else:
            location_name = location
        print('Moving to:',location_name)

        if self.location == location_name:
            print('Already in {} position'.format(location_name))
            return
        available_locations = list(self.calibration_data.keys()) + ['_'.join(['above',k]) for k in self.calibration_data.keys()]
        if location not in available_locations:
            print('{} not present in calibration data')
            return

        if check:
            self.move_dobot(self.current_coords['x'],self.current_coords['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.calibration_data[location]['z'] + 20)
            if not self.ask_yes_no(message="Is the tip 20mm above the target? (y/n)"):
                self.calibration_data[location]['z'] += 20

        if direct == False and height == 'exact':
            self.move_dobot(self.current_coords['x'],self.current_coords['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.calibration_data[location]['z'])
        elif direct == True and height == 'exact':
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.calibration_data[location]['z'])

        elif direct == False and height == 'above':
            self.move_dobot(self.current_coords['x'],self.current_coords['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.height)
        elif direct == False and height == 'above_side':
            self.move_dobot(self.current_coords['x'],self.current_coords['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y']-30, self.height)
        elif direct == True and height == 'above':
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.height)

        elif direct == False and height == 'close':
            self.move_dobot(self.current_coords['x'],self.current_coords['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.height)
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.calibration_data[location]['z'] + 30)
        elif direct == True and height == 'close':
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y'], self.calibration_data[location]['z'] + 30)
        self.location = location_name
        return

    def move_dobot(self,x,y,z,verbose=True,check=False):
        '''
        Takes a set of XYZ coordinates and moves the Dobot to that location
        '''
        if verbose:
            print('Dobot moving...',end='')
        if check:
            z += 20
        if not self.sim:
            last_index = dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVJXYZMode, x,y,z,0, isQueued = 1)
            self.run_cmd()
        self.current_coords = {'x':float(x),'y':float(y),'z':float(z)}
        if verbose:
            print('Current position: x={}\ty={}\tz={}'.format(round(x,2),round(y,2),round(z,2)))
        return

    def move_to_well(self,row,column):
        '''
        Moves the Dobot to a defined well while checking that the well is within
        the bounds of the plate
        '''
        if self.location != 'print':
            self.move_to_location(location='print')

        if row <= self.max_rows and column <= self.max_columns and row >= 0 and column >= 0:
            target_coords = self.get_well_coords(row,column)
            print('Moving to well {}-{}'.format(row,column))
            self.move_dobot(target_coords['x'],target_coords['y'],target_coords['z'],verbose=False)
            self.current_row = row
            self.current_column = column
            self.update_monitor()
            return
        else:
            print("Well out of range")
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
        step_num = len(possible_steps)*10
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
            else:
                print(f'{key} is not a valid input')
            self.move_dobot(x,y,z)
        return

    def check_for_pause(self):
        if self.pause:
            print('Process has been paused')
            if self.ask_yes_no(message="Quit print? (y/n)"):
                print('Quitting\n')
                self.pause = False
                return True
        self.pause = False
        return False

    def print_array(self):

        if not self.ask_yes_no(message="Print an array? (y/n)"):
            return

        all_exp = self.get_all_paths('Print_arrays/*/',base=True)
        experiment_folder = select_options(all_exp,message='Select one of the experiments:',trim=True)

        all_arrays = self.get_all_paths('{}/*.csv'.format(experiment_folder))
        all_arrays = [p for p in all_arrays if 'key' not in p]
        chosen_path = select_options(all_arrays,message='Select one of the arrays:',trim=True)

        self.move_to_location(location='print')
        arr = pd.read_csv(chosen_path)
        for index, line in arr.iterrows():
            print('\nOn {} out of {}'.format(index+1,len(arr)))
            time.sleep(0.5)
            if self.check_for_pause(): return
            self.move_to_well(line['Row'],line['Column'])
            self.print_droplets_current(line['Droplet'])
        print('\nPrint array complete\n')
        return


    def print_large_volumes(self):
        if not self.ask_yes_no(message="Print a large volume array? (y/n)"):
            return

        all_arr = self.get_all_paths('Print_arrays/large_volume_arrays/*.csv',base=True)
        chosen_path = select_options(all_arr, message='Select one of the following arrays:',trim=True)

        if not self.calibrated:
            print('The pipet is currently not calibrated, please calibrate it')
            return

        num_asps = int(round(((self.max_volume - self.current_volume) / self.vol_per_asp),0))
        print(f'Filling tip from {self.current_volume}...{num_asps}')
        self.move_to_location(location='tube')
        self.print_droplets(self.frequency,0,self.refuel_width ,num_asps,aspiration=True)

        self.move_to_location(location='print')
        arr = pd.read_csv(chosen_path)
        for index, line in arr.iterrows():
            if self.check_for_pause(): return
            if self.current_volume < self.min_volume:
                num_asps = int(round(((self.max_volume - self.current_volume) / self.vol_per_asp),0))
                print(f'Refilling...{num_asps}')
                self.move_to_location(location='tube')
                self.print_droplets(self.frequency,0,self.refuel_width,num_asps,aspiration=True)
                print('returning to print...')
                self.move_to_location(location='print')
            print('\nOn {} out of {} with {}'.format(index+1,len(arr),self.current_volume))
            self.move_to_well(line['Row'],line['Column'])
            self.print_droplets(self.frequency,self.pulse_width,0,line['Droplet'])
        print('\nPrint array complete\n')
        return

    def drive_platform(self):
        '''
        Comprehensive manually driving function. Within this method, the
        operator is able to move the dobot by wells, load and unload the
        gripper, set and control pressures, and print defined arrays
        '''
        section_break()
        print("Driving platform...")

        while True:
            self.keyboard_config = 'General platform'
            self.update_monitor()
            key = self.get_current_key()
            if key == Key.up:
                self.move_to_well(self.current_row - 1, self.current_column)
            elif key == Key.down:
                self.move_to_well(self.current_row + 1, self.current_column)
            elif key == Key.left:
                self.move_to_well(self.current_row, self.current_column - 1 )
            elif key == Key.right:
                self.move_to_well(self.current_row, self.current_column + 1)
            elif key == 'g':
                self.load_gripper()
            elif key == 'p':
                self.move_to_location(location='print')
            elif key == 'l':
                self.move_to_location(location='loading')
            # elif key == '[':
            #     self.move_to_location(location='tube')
            # elif key == ']':
            #     self.move_to_location(location='tube',height='above')
            elif key == 'y':
                self.change_print_position()
            elif key == 'h':
                # self.change_position(location='loading')
                self.change_position()
            elif key == 't':
                self.print_droplets_current(10)
            elif key == 'T':
                for i in range(5):
                    self.print_droplets_current(20)
                    time.sleep(0.5)
            elif key == 'o':
                self.pressure_on()
            elif key == 'i':
                self.pressure_off()
            elif key == 'u':
                self.set_pressure(1.1,-5)
            elif key == 'j':
                self.set_pressure(2,0.3)
            elif key == 'M':
                self.select_mode()
            # elif c == 'r':
            #     self.pressure_test()
            elif key == 'x':
                self.refuel_test()
            elif key == 'c':
                self.pulse_test()
            elif key == 'C':
                self.calibrate_pipet()
            elif key == 'b':
                # self.check_pressures()
                self.calibrate_chip()
            elif key == 'B':
                # self.get_pressure()
                self.resistance_testing()
            # elif c == 'r':
            #     self.record_flow()
            elif key == 'r':
                self.reset_dobot_position()
            elif key == 'P':
                self.print_array()
            elif key == 'V':
                self.print_large_volumes()
            elif key == 'n':
                self.dobot_manual_drive()
            elif key == '!':
                self.move_to_location()
            # elif c == ']':
            #     self.refuel_open()
            # elif c == ';':
            #     self.pulse_open()
            # elif c == '.':
            #     self.close_valves()
            elif key == ';':
                self.pulse_width += 500
                print('Current pulse width: ',self.pulse_width)
            elif key == '.':
                self.pulse_width -= 500
                print('Current pulse width: ',self.pulse_width)
            elif key == '1':
                self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.1)
            elif key == '2':
                self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.01)
            elif key == '3':
                self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.01)
            elif key == '4':
                self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.1)

            elif key == '6':
                self.set_pressure(self.pulse_pressure - 0.1,self.refuel_pressure)
            elif key == '7':
                self.set_pressure(self.pulse_pressure - 0.01,self.refuel_pressure)
            elif key == '8':
                self.set_pressure(self.pulse_pressure + 0.01,self.refuel_pressure)
            elif key == '9':
                self.set_pressure(self.pulse_pressure + 0.1,self.refuel_pressure)
            elif key == "q":
                if self.ask_yes_no(message='Quit (y/n)'):
                    print('Quitting...')
                    section_break()
                    return
                else:
                    print("Didn't quit")
            else:
                print('Please enter a valid key, not:',key)

    def disconnect_dobot(self):
        if not self.sim:
            self.deactivate_gripper()
            dType.SetQueuedCmdStopExec(self.api)
            dType.DisconnectDobot(self.api)
        print('Disconnected Dobot')
        return

    def init_ard(self,port):
        print('\nInitizing arduino...')
        if not self.sim:
            self.ser = serial.Serial(port=port, baudrate=115200, bytesize=8, parity='N', stopbits=1, xonxoff=0, timeout=0)
            time.sleep(1)
        print('Arduino is connected')
        return

    def print_droplets_current(self,count):
        self.print_droplets(self.frequency,self.pulse_width,self.refuel_width,count)
        return

    def print_droplets(self,freq,pulse_width,refuel_width,count,aspiration=False):
        '''
        Sends the desired printing instructions to the Arduino
        '''
        print('starting print... ',end='')
        if self.sim:
            print('simulated print:',freq,pulse_width,refuel_width,count)
            if self.tracking_volume:
                print('Volume tracking')
                if aspiration:
                    self.current_volume += (self.vol_per_asp * count)
                else:
                    self.current_volume -= (self.vol_per_disp * count)
                print('Current volume: ',self.current_volume)
            return
        if count == 0:
            print('No droplets to print')
            return
        delay = (count/freq)
        # self.get_pressure()
        extra = self.ser.readall().decode()
        self.ser.write(SetParam_CtrlSeq(freq,pulse_width,refuel_width,count))
        time.sleep(0.2)
        self.ser.write(Switch_CtrlSeq('close'))

        time.sleep(delay)
        current = self.ser.read().decode()
        i = 0
        while current != 'C':
            current = self.ser.read().decode()
            time.sleep(0.05)
            i += 1
            if i > 10:
                print('\n---Missed the signal, repeating print---\n')
                self.print_droplets(freq,pulse_width,refuel_width,count)
                print('Completed the fix for the missed signal')
                break
        print(' - Count: ',i)
        time.sleep(0.1)
        after = self.ser.readall().decode()
        if 'N' in after or 'F' in after:
            print('\n---Incorrect parameters, repeating print---\n')
            self.print_droplets(freq,pulse_width,refuel_width,count)
            print('Completed the fix for the incorrect parameters')
            return
        # self.get_pressure()
        if self.tracking_volume:
            print('Volume tracking')
            if aspiration:
                self.current_volume += (self.vol_per_asp * count)
            else:
                self.current_volume -= (self.vol_per_disp * count)
            print('Current volume: ',self.current_volume)
        print('print complete')
        return

    def refuel_test(self):
        '''
        Defined printing protocol used in calibration
        '''
        print('Refuel test')
        self.print_droplets(self.frequency,0,self.refuel_width,self.test_droplet_count)
        return

    def pulse_test(self):
        '''
        Defined printing protocol used in calibration
        '''
        print('Pulse test')
        self.print_droplets(self.frequency,self.pulse_width,0,self.test_droplet_count)
        return

    def close_ard(self):
        if not self.sim:
            self.ser.close()
        print('Disconnected Arduino')
        return

    def init_pressure(self):
        '''
        Initiates the Precigenome pressure regulator and the two different
        channels used
        '''
        print("\nConnecting pressure regulator...")
        if not self.sim:
            self.mcfs = PGMFC()
            self.mcfs.monitor_start(span=100)
            time.sleep(1)
            self.channel_pulse = self.mcfs[2]
            self.channel_refuel = self.mcfs[1]
        print('Pressure regulator is connected')

        self.set_pressure(self.pulse_pressure,self.refuel_pressure)
        return

    def set_pressure(self,pulse,refuel,runtime=6000):
        self.pulse_pressure = pulse
        self.refuel_pressure = refuel
        if not self.sim:
            self.channel_pulse.set_params(peak=pulse,runtime=runtime)
            self.channel_refuel.set_params(peak=refuel,runtime=runtime)
        print("Setting pressure: Pulse={}\tRefuel={}".format(pulse,refuel))
        return

    def get_pressure(self):
        if not self.sim:
            self.print_pressure = self.channel_pulse.get_pressure()
            self.refuel_pressure = self.channel_refuel.get_pressure()
        print("Current pressure: Pulse={}\tRefuel={}".format(self.pulse_pressure,self.refuel_pressure))
        return

    def pulse_on(self):
        if not self.sim:
            self.channel_pulse.purge_on()
        return

    def refuel_on(self):
        if not self.sim:
            self.channel_refuel.purge_on()
        return

    def pulse_off(self):
        if not self.sim:
            self.channel_pulse.purge_off()
        return

    def refuel_off(self):
        if not self.sim:
            self.channel_refuel.purge_off()
        return

    def pressure_on(self):
        print('Both pressures on: pulse={}\t refuel={}'.format(self.pulse_pressure,self.refuel_pressure))
        self.pulse_on()
        self.refuel_on()
        return

    def pressure_off(self):
        print('Both pressures off')
        self.pulse_off()
        self.refuel_off()
        return

    def close_reg(self):
        if not self.sim: self.mcfs.close()
        return

    def charge_chip(self):
        print('\nAdjust pressure:')
        self.keyboard_config = 'Printer head charging'
        self.update_monitor()
        while True:
            c = self.get_current_key()
            if c == 'x':
                self.refuel_test()
            elif c == 'c':
                self.pulse_test()
            elif c =='t':
                self.print_droplets_current(10)
            elif c =='T':
                self.test_print()
            elif c == '1':
                self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.1)
            elif c == '2':
                self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.01)
            elif c == '3':
                self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.01)
            elif c == '4':
                self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.1)
            elif c == '6':
                self.set_pressure(self.pulse_pressure - 0.1,self.refuel_pressure)
            elif c == '7':
                self.set_pressure(self.pulse_pressure - 0.01,self.refuel_pressure)
            elif c == '8':
                self.set_pressure(self.pulse_pressure + 0.01,self.refuel_pressure)
            elif c == '9':
                self.set_pressure(self.pulse_pressure + 0.1,self.refuel_pressure)
            elif c == '[':
                self.move_to_location(location='tube')
            elif c == ']':
                self.move_to_location(location='tube',height='above')

            elif c == "q":
                if self.ask_yes_no(message='Finished charging? (y/n)'):
                    print('Quitting...')
                    section_break()
                    return
                else:
                    print("Didn't quit")
            else:
                print("not valid")
        return

    def test_print(self):
        for i in range(5):
            self.print_droplets_current(20)
            time.sleep(0.5)
        return

    def test_pressure(self,print_pressure):
        self.set_pressure(print_pressure,1)
        self.move_to_location(location='tube')
        self.charge_chip()
        self.set_pressure(self.pulse_pressure,print_pressure/12)

        self.move_to_location(location='tube',height='above')
        input('Tare the scale, place tube in holder, and press Enter')
        self.move_to_location(location='tube')
        self.test_print()
        self.move_to_location(location='tube',height='above')

        current_vol =self.ask_for_number(message='Enter mg of liquid printed: ')
        input('Place tube back in holder and press enter')
        return current_vol


    def calibrate_chip(self,target = 6):
        if not self.ask_yes_no(message='Calibrate chip? (y/n)'):
            print('Quitting...')
            section_break()
            return
        self.calibrate_print(target=target)
        input('Place tube back in holder and press enter')
        print('\n---Calibrate the refuel pressure---')
        self.set_pressure(self.pulse_pressure,self.pulse_pressure/8)
        self.charge_chip()
        print('\nCompleted calibration')
        section_break()
        return


    def calibrate_print(self,target = 6):
        x = []
        y = []

        if self.ask_yes_no(message='Printing WCE? (y/n)'):
            print('printing wce...')
            current_print = 3.5
            charge_refuel = 1.2
        else:
            current_print = 2
            charge_refuel = 0.6
        tolerance = 0.05

        while True:
            print('Current measurements:{}\t{}'.format(x,y))
            current_vol = self.test_pressure(current_print)
            if current_vol <= target*(1+tolerance) and current_vol >= target*(1-tolerance):
                print('Volume is within tolerance')
                return
            answer = self.ask_yes_no_quit(message='y: add point\tn: repeat test,\tq: quit')
            if answer == 'quit':
                print('Quitting calibration')
                return
            elif answer == 'yes':
                print('Adding measurement')
                x.append(self.pulse_pressure)
                y.append(current_vol)
            elif answer == 'no':
                print('Skipping measurement')
            if len(x) == 1:
                if current_vol > target:
                    current_print = self.pulse_pressure - 0.5
                else:
                    current_print = self.pulse_pressure + 0.5
                print('--- Setting pressure to ',current_print)

            else:
                [m,b] = np.polyfit(np.array(x),np.array(y),1)
                current_print = (target - b) / m
                print('Setting pressure to ',current_print)
        return

    def calibrate_pipet_aspiration(self):
        self.move_to_location(location='tube',height='above_side')
        input('Tare the tube, place tube in holder, and press Enter ')
        self.move_to_location(location='tube')
        refuel_counter = 0
        hold = True
        self.keyboard_config = 'Pipet Charging'
        self.update_monitor()
        print("Press x to aspriate reagent until pipet is nearly full, then press q")
        while hold:
            key = self.get_current_key()
            if key == "x":
                refuel_counter += 1
                self.refuel_test()
            elif key == "q":
                if self.ask_yes_no(message='Pipet tip full? (y/n)'):
                    hold = False
                else:
                    print("Didn't quit")
        self.move_to_location(location='tube',height='above_side')
        self.current_volume = ask_for_number(message='Enter mg of liquid aspirated: ')
        self.vol_per_asp = self.current_volume / refuel_counter
        print('Volume aspirated per pulse:',self.vol_per_asp,'\n')
        return

    def calibrate_pipet_dispense(self,target=18):
        tolerance = 0.05
        x = []
        y = []
        hold = True
        current_print = self.pulse_pressure

        while hold:
            self.set_pressure(current_print,self.refuel_pressure)
            self.move_to_location(location='tube',height='close')

            print_test_count = 5
            for i in range(print_test_count):
                self.pulse_test()

            self.move_to_location(location='tube',height='above_side')
            dispensed = ask_for_number(message='\nEnter mg of liquid dispensed: ')
            self.current_disp_volume = dispensed / print_test_count
            self.current_volume -= dispensed
            print(f'Current volume {self.current_volume}')

            if self.current_disp_volume <= target*(1+tolerance) and self.current_disp_volume >= target*(1-tolerance):
                print('Volume is within tolerance, Calibration complete')
                self.calibrated = True
                self.tracking_volume = True
                self.vol_per_disp = target
                print(f'Volume per dispense is set to: {self.vol_per_disp}')
                return
            else:
                answer = self.ask_yes_no_quit(message='y: add point\tn: repeat test,\tq: quit')
                if answer == 'quit':
                    print('Quitting calibration')
                    return
                elif answer == 'yes':
                    print('Adding measurement')
                    x.append(self.pulse_pressure)
                    y.append(self.current_disp_volume)
                elif answer == 'no':
                    print('Skipping measurement')
                if len(x) == 1:
                    if self.current_disp_volume > target:
                        current_print = self.pulse_pressure - 0.25
                    else:
                        current_print = self.pulse_pressure + 0.25
                    print('--- Setting pressure to ',current_print)
                else:
                    [m,b] = np.polyfit(np.array(x),np.array(y),1)
                    current_print = (target - b) / m
                    print('Setting pressure to ',current_print)

    def calibrate_pipet(self,target=18):
        if not self.ask_yes_no(message='Calibrate pipet? (y/n)'):
            print('Quitting...')
            return
        if self.mode != 'p1000':
            print('Must be in p1000 mode to execute this calibration')
            return
        self.calibrate_pipet_aspiration()
        self.calibrate_pipet_dispense(target=target)
        return


    def check_pressures(self):
        self.move_to_location(location='tube')
        print('\nCheck the refuel pressure\n')
        hold = True
        while hold:
            try:
                c = msvcrt.getch().decode()
                print(c)
                valid = True
            except:
                print('Not a valid input')
                valid = False
            if valid:
                if c == "x":
                    self.refuel_test()
                elif c == "c":
                    self.pulse_test()
                elif c == 'z':
                    self.print_droplets_current(10)
                    print('completed test print')

                elif c == '1':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.1)
                elif c == '2':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.01)
                elif c == '3':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.01)
                elif c == '4':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.1)

                elif c == '6':
                    self.set_pressure(self.pulse_pressure - 0.1,self.refuel_pressure)
                elif c == '7':
                    self.set_pressure(self.pulse_pressure - 0.01,self.refuel_pressure)
                elif c == '8':
                    self.set_pressure(self.pulse_pressure + 0.01,self.refuel_pressure)
                elif c == '9':
                    self.set_pressure(self.pulse_pressure + 0.1,self.refuel_pressure)

                elif c == "q":
                    if self.ask_yes_no(message='Test droplet volume? (y/n)'):
                        hold = False
                    else:
                        print("Didn't quit")
                else:
                    print("Not a valid input")

        # chip.real_refuel_pressure = self.refuel_pressure
        print('Adjusted refuel:',self.refuel_pressure)
        print('Adjusted print:',self.pulse_pressure)

        self.move_to_location(location='tube',height='above')
        input('\nZero the scale and press Enter\n')
        self.move_to_location(location='tube')
        droplet_count = 100
        print("Printing {} droplets...".format(droplet_count))
        for i in range(5):
            self.print_droplets_current(20)
            time.sleep(0.5)
        self.move_to_location(location='tube',height='above')

        test_mass = float(input('\nType in the mass press Enter\n'))
        # test_volume = test_mass / chip.density

        # chip.set_droplet_volume((test_volume / droplet_count) *1000)

        # print('\nCurrent droplet volume = {}\n'.format(chip.real_volume))

        if self.ask_yes_no(message='Repeat test? (y/n)'):
            # self.move_to_location(location='tube')
            self.check_pressures()
            return
        else:
            print('Calibration complete')
            return
        return

    def record_flow(self):
        pulse_flow_data = []
        refuel_flow_data = []
        for i in range(100):
            pulse_flow_data.append(self.channel_pulse.get_airflowrate()[0])
            refuel_flow_data.append(self.channel_refuel.get_airflowrate()[0])

            if pulse_flow_data[i] > 60000:
                pulse_flow_data[i] -= 65536
            if refuel_flow_data[i] > 60000:
                refuel_flow_data[i] -= 65536

            if i % 10 == 0 and i != 0:
                avg_pulse = round(np.mean(pulse_flow_data[i-10:i]),3)
                avg_refuel = round(np.mean(refuel_flow_data[i-10:i]),3)
                # print("On {}:\tP:{}\tR:{}\t||\tP:{}\tR:{}".format(avg_pulse,avg_refuel,self.channel_pulse.get_pressure(),self.channel_refuel.get_pressure()))
                print("On {}:\tP:{}\tR:{}".format(i,avg_pulse,avg_refuel))

            time.sleep(.1)
        print("Press enter to proceed")
        input()

    def refuel_open(self):
        if not self.ask_yes_no(message='Open refuel valve? (y/n)'):
            print('Quitting...')
            section_break()
            return
        if not self.sim: self.ser.write(Switch_CtrlSeq('refuel'))
        return

    def pulse_open(self):
        if not self.ask_yes_no(message='Open printing valve? (y/n)'):
            print('Quitting...')
            section_break()
            return
        if not self.sim: self.ser.write(Switch_CtrlSeq('pulse'))
        return

    def quick_eject(self):
        print('Quick ejecting')
        print_droplets(self.frequency,0,0,10)
        return

    def close_valves(self):
        if not self.sim: self.ser.write(Switch_CtrlSeq('close'))
        return

    def pressure_test(self):
        if not self.ask_yes_no(message="Test the pressure regulator? (y/n)"):
            return
        print("Load the dummy printer head")
        self.load_gripper()

        self.set_pressure(10,10)
        self.pressure_on()
        self.record_flow()

        self.refuel_open()
        self.pulse_open()
        self.record_flow()

        self.close_valves()
        self.record_flow()

        self.refuel_open()
        self.pulse_open()
        self.record_flow()

        self.close_valves()
        self.record_flow()
        return










#
