# from Precigenome.PGMFC import PGMFC

import Robot, Arduino, Regulator, Monitor
from utils import *

import time
import sys
import msvcrt
import json
import numpy as np
import pandas as pd
import math
import glob
import os
from pynput import keyboard
from pynput.keyboard import Key
from pyautogui import press
import datetime
import shutil


class Platform(Robot.Robot, Arduino.Arduino, Regulator.Regulator):
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
        self.monitor = Monitor.Monitor()
        self.keyboard_config = 'empty'
        self.location = 'unknown'
        self.current_row = 0
        self.current_column = 0
        time.sleep(0.5)
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
        if key == keyboard.Key.backspace:
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
                    press('esc')
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
            elif key == Key.esc:
                continue
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
            elif key == Key.esc:
                continue
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
        self.test_droplet_count_low = self.default_settings['dispenser_types'][mode]['test_droplet_count_low']
        self.test_droplet_count_high = self.default_settings['dispenser_types'][mode]['test_droplet_count_high']
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

    def change_print_position(self):
        '''
        Initiates a protocol to modify the expected well locations of a given
        plate. Moves from corner to corner allowing the operator to manually
        drive the dobot to correct any deviations. Once all the points are
        corrected, the new positions are stored in the plate metadata file.
        '''
        if not self.ask_yes_no(message="Change print position? (y/n)"): return
        self.move_to_location(location='print')
        self.move_dobot(self.top_left['x'], self.top_left['y'], self.top_left['z'])
        self.dobot_manual_drive()

        self.top_left = self.current_coords
        self.calibration_data['print'] = {'x':float(self.top_left['x']),'y':float(self.top_left['y']),'z':float( self.top_left['z'])}

        self.move_dobot(self.top_right['x'], self.top_right['y'], self.top_right['z'])
        self.dobot_manual_drive()

        self.top_right = self.current_coords

        self.move_dobot(self.bottom_right['x'], self.bottom_right['y'], self.bottom_right['z'])
        self.dobot_manual_drive()

        self.bottom_right = self.current_coords

        self.move_dobot(self.bottom_left['x'], self.bottom_left['y'], self.bottom_left['z'])
        self.dobot_manual_drive()

        self.bottom_left = self.current_coords
        self.corners = np.array([self.get_coords(self.top_left)[:2],self.get_coords(self.top_right)[:2],self.get_coords(self.bottom_right)[:2],self.get_coords(self.bottom_left)[:2]], dtype = "float32")
        self.gen_trans_matrix()

        self.row_z_step = (self.bottom_left['z'] - self.top_left['z']) / (self.max_rows )
        self.col_z_step =  (self.top_right['z'] - self.top_left['z']) / (self.max_columns)

        self.write_plate_data()
        return

    def change_position(self,location=False):
        if not location:
            location,quit = select_options(list(self.calibration_data.keys()))
            if quit: return
        if not location in self.calibration_data.keys():
            print('{} not present in calibration data')
            return
        self.move_to_location(location=location,check=True)
        self.dobot_manual_drive()
        self.calibration_data[location] = self.current_coords
        self.write_printing_calibrations()
        return

    def move_to_location(self,location=False,height='exact',direct=False,check=False):
        print('Current',self.location)
        if not location:
            location,quit = select_options(list(self.calibration_data.keys()))
            if quit: return
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
            print(f'{location} not present in calibration data')
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
            self.move_dobot(self.calibration_data[location]['x'],self.calibration_data[location]['y']+30, self.height)
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

    def check_for_pause(self):
        if self.pause:
            print('Process has been paused')
            self.pause = False
            return True
        self.pause = False
        return False

    def refill_chip(self):
        print('\nTime to refill the chip...')
        self.move_to_location('loading')
        self.load_gripper()
        input('Press enter when ready to resume')
        return

    def print_array(self):

        if not self.ask_yes_no(message="Print an array? (y/n)"):
            return

        all_exp = self.get_all_paths('Print_arrays/*/',base=True)
        experiment_folder,quit = select_options(all_exp,message='Select one of the experiments:',trim=True)
        if quit: return
        all_arrays = self.get_all_paths('{}/*.csv'.format(experiment_folder))
        all_arrays = [p for p in all_arrays if 'key' not in p]
        chosen_path,quit = select_options(all_arrays,message='Select one of the arrays:',trim=True)
        if quit: return

        self.move_to_location(location='print')
        arr = pd.read_csv(chosen_path)
        droplets_printed = 0
        for index, line in arr.iterrows():
            if droplets_printed > 2000:
                self.refill_chip()
                droplets_printed = 0
            print('\nOn {} out of {}-droplets:{}'.format(index+1,len(arr),droplets_printed))
            time.sleep(0.1)
            if self.check_for_pause():
                if self.ask_yes_no(message="Quit print? (y/n)"):
                    print('Quitting\n')
                    return
                if self.ask_yes_no(message="Refill chip? (y/n)"):
                    self.refill_chip()
                    droplets_printed = 0
            self.move_to_well(line['Row'],line['Column'])
            if not self.print_droplets_current(line['Droplet']):
                print('Quitting print array')
                return
            droplets_printed += line['Droplet']

            if 'partial' in chosen_path:
                partial_path = ''.join([chosen_path[:-4],'.csv'])
            else:
                partial_path = ''.join([chosen_path[:-4],'-partial','.csv'])

            print(partial_path)
            arr.iloc[index+1:].to_csv(partial_path)

        print('\nPrint array complete\n')
        dir_path = r'{}\completed_arrays\\'.format(experiment_folder)
        print('Dir:',dir_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        print('Dir:',dir_path)

        if 'partial' in chosen_path:
            original_path = ''.join(partial_path.split('-partial'))
            print(original_path)
            new_path = '{}\{}'.format(dir_path,str(original_path).split('\\')[-1])
            shutil.move(original_path,new_path)
        else:
            new_path = '{}\{}'.format(dir_path,str(chosen_path).split('\\')[-1])
            print(new_path)
            shutil.move(chosen_path,new_path)

        os.remove(partial_path)
        self.move_to_location(location='loading')
        return

    def print_large_volumes(self):
        if not self.ask_yes_no(message="Print a large volume array? (y/n)"):
            return

        all_arr = self.get_all_paths('Print_arrays/large_volume_arrays/*.csv',base=True)
        chosen_path, quit = select_options(all_arr, message='Select one of the following arrays:',trim=True)
        if quit: return

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
            if self.check_for_pause():
                if self.ask_yes_no(message="Quit print? (y/n)"):
                    print('Quitting\n')
                    return
            if self.current_volume < self.min_volume:
                num_asps = int(round(((self.max_volume - self.current_volume) / self.vol_per_asp),0))
                print(f'Refilling...{num_asps}')
                self.move_to_location(location='tube')
                input('\nPress enter when ready for aspiration')
                if not self.print_droplets(self.frequency,0,self.refuel_width,num_asps,aspiration=True):
                    print('Quitting print array')
                    return
                print('returning to print...')
                self.move_to_location(location='print')
            print('\nOn {} out of {} with {}'.format(index+1,len(arr),self.current_volume))
            self.move_to_well(line['Row'],line['Column'])
            self.print_droplets(self.frequency,self.pulse_width,0,line['Droplet'])
            if not self.print_droplets(self.frequency,self.pulse_width,0,line['Droplet']):
                print('Quitting print array')
                return
            if 'partial' in chosen_path:
                new_path = ''.join([chosen_path[:-4],'.csv'])
            else:
                new_path = ''.join([chosen_path[:-4],'-partial','.csv'])
            print(new_path)
            arr.iloc[index:].to_csv(new_path)

        print('\nPrint array complete\n')
        os.remove(new_path)
        self.move_to_location(location='loading')
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
            elif key == '[':
                self.move_to_location(location='tube')
            elif key == ']':
                self.move_to_location(location='tube',height='above_side')
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
            elif key == 'z':
                self.refuel_test(high=True)
            elif key == 'v':
                self.pulse_test(high=True)
            elif key == 'C':
                if self.mode == 'p1000':
                    self.calibrate_pipet()
                elif self.mode == 'droplet':
                    self.calibrate_chip()
            elif key == 'B':
                # self.get_pressure()
                self.resistance_testing()
            # elif c == 'r':
            #     self.record_flow()
            # elif key == 'r':
            #     self.reset_dobot_position()
            elif key == 'P':
                if self.mode == 'p1000':
                    self.print_large_volumes()
                elif self.mode == 'droplet':
                    self.print_array()
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
            # elif key == ';':
            #     self.pulse_width += 500
            #     print('Current pulse width: ',self.pulse_width)
            # elif key == '.':
            #     self.pulse_width -= 500
            #     print('Current pulse width: ',self.pulse_width)
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
            elif key == "S":
                print('\nPaused keyboard tracking. Press Enter when finished\n')
                input()
                print("Returning to tracking\n")
            elif key == Key.esc:
                continue
            elif key == "q":
                if self.ask_yes_no(message='Quit (y/n)'):
                    print('Quitting...')
                    section_break()
                    return
                else:
                    print("Didn't quit")
            else:
                print('Please enter a valid key, not:',key)


    def print_droplets_current(self,count):
        return self.print_droplets(self.frequency,self.pulse_width,self.refuel_width,count)

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

        ## Pressure check
        self.compare_pressures(verbose=True)

        i = 0
        while self.correct_pressure == False:
            verbose = False
            if i % 10 == 0:
                print('Pressure is incorrect')
                verbose = True
            time.sleep(0.2)
            self.compare_pressures(verbose=verbose)
            if self.check_for_pause():
                if self.ask_yes_no(message="Quit print? (y/n)"):
                    print('Quitting\n')
                    return False
                if self.ask_yes_no(message="Print Anyway? (y/n)"):
                    print('Continuing with print...\n')
                    self.correct_pressure = True
            print('.',end='')
            i += 1

        delay = (count/freq)
        extra = self.read_ard()

        self.print_command(freq,pulse_width,refuel_width,count)

        time.sleep(delay)
        current = self.read_ard()
        i = 0
        while 'C' not in current:
            current = self.read_ard()
            time.sleep(0.05)
            i += 1
            if i > 20:
                print('\n---Missed the signal, repeating print---\n')
                self.print_droplets(freq,pulse_width,refuel_width,count)
                print('Completed the fix for the missed signal')
                break
        print(' - Count: ',i)
        time.sleep(0.1)
        after = self.read_ard()

        if 'N' in after or 'F' in after:
            print('\n---Incorrect parameters, repeating print---\n')
            self.print_droplets(freq,pulse_width,refuel_width,count)
            print('Completed the fix for the incorrect parameters')
            return True

        self.update_pressure(verbose=True)
        if self.tracking_volume:
            print('Volume tracking')
            if aspiration:
                self.current_volume += (self.vol_per_asp * count)
            else:
                self.current_volume -= (self.vol_per_disp * count)
            print('Current volume: ',self.current_volume)
        print('print complete')
        return True

    def refuel_test(self,high=False,count=0):
        '''
        Defined printing protocol used in calibration
        '''
        print('Refuel test')
        if high:
            self.print_droplets(self.frequency,0,self.refuel_width,self.test_droplet_count_high)
        else:
            if count == 0:
                self.print_droplets(self.frequency,0,self.refuel_width,self.test_droplet_count_low)
            else:
                self.print_droplets(self.frequency,0,self.refuel_width,count)
        return

    def pulse_test(self,high=False,count=0):
        '''
        Defined printing protocol used in calibration
        '''
        print('Pulse test')
        if high:
            self.print_droplets(self.frequency,self.pulse_width,0,self.test_droplet_count_high)
        else:
            if count == 0:
                self.print_droplets(self.frequency,self.pulse_width,0,self.test_droplet_count_low)
            else:
                self.print_droplets(self.frequency,self.pulse_width,0,count)
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
            elif c == Key.esc:
                continue
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

        current_vol = ask_for_number(message='Enter mg of liquid printed: ')
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
                if len(x) == 1:
                    current_print = (target/current_vol) * self.pulse_pressure
                    print('--- Setting pressure to ',current_print)
                else:
                    [m,b] = np.polyfit(np.array(x),np.array(y),1)
                    current_print = (target - b) / m
                    print('Setting pressure to ',current_print)
            elif answer == 'no':
                print('Skipping measurement')

        return

    # def reset_pipet_aspiration(self):
    #     self.set_pressure(3,self.refuel_pressure)
    #     self.move_to_location(location='tube',height='close')
    #     hold = True
    #     while hold:
    #         key = self.get_current_key()
    #         if key == "c":
    #             self.pulse_test()
    #         elif key == "v":
    #             self.pulse_test(count=5)
    #         elif key == "q":
    #             if self.ask_yes_no(message='Pipet tip empty? (y/n)'):
    #                 hold = False
    #             else:
    #                 print("Didn't quit")
    #     self.set_pressure(,self.refuel_pressure)
    #     self.move_to_location(location='tube',height='above_side')
    #     input('Tare the tube, place tube in holder, and press Enter ')
    #     self.move_to_location(location='tube')
    #     refuel_counter = 0
    #     hold = True
    #     self.keyboard_config = 'Pipet Charging'
    #     self.update_monitor()
    #     print("Press x to aspriate reagent until pipet is nearly full, then press q")
    #     while hold:
    #         key = self.get_current_key()
    #         if key == "x":
    #             refuel_counter += 1
    #             self.refuel_test()
    #         elif key == "q":
    #             if self.ask_yes_no(message='Pipet tip full? (y/n)'):
    #                 hold = False
    #             else:
    #                 print("Didn't quit")
    #     self.move_to_location(location='tube',height='above_side')
    #     self.current_volume = ask_for_number(message='Enter mg of liquid aspirated: ')
    #     self.vol_per_asp = self.current_volume / refuel_counter
    #     print('Volume aspirated per pulse:',self.vol_per_asp,'\n')
    #     return

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
            if key == "z":
                refuel_counter += self.test_droplet_count_high
                self.refuel_test(high=True)
            elif key == Key.esc:
                continue
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


    def quick_eject(self):
        print('Quick ejecting')
        print_droplets(self.frequency,0,0,10)
        return











#
