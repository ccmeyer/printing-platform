import Dobot.DobotDllType as dType
from Precigenome.PGMFC import PGMFC

import time
import serial
import sys
import msvcrt
import json
import numpy as np
import math
import cv2

def ask_yes_no():
    '''
    Simple function to double check that the operator wants to commit to an action
    '''
    possible = ['y','n']
    while True:
        c = msvcrt.getch().decode()
        if c not in possible:
            print('Choose a valid key')
        elif c == 'y':
            return True
        elif c == 'n':
            return False

def run_cmd(api,last_index):
    '''
    Executes the dobot's queued commands
    '''
    dType.SetQueuedCmdStartExec(api)
    #Wait for Executing Last Command
    while last_index[0] > dType.GetQueuedCmdCurrentIndex(api)[0]:
        dType.dSleep(100)

    #Stop to Execute Command Queued
    dType.SetQueuedCmdStopExec(api)
    return


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

def Switch_CtrlSeq(switchstate):
    '''
    Signals to the Arduino that the printing command is complete
    '''
    single_Ctrl=[]
    if switchstate == 1:
        single_Ctrl = [255,255,239,239]
    else:
        single_Ctrl = [255,255,254,254]
    return bytes(single_Ctrl)

def get_coords(coords):
    '''
    Converts the coordinates stored in a dictionary to a numpy array
    '''
    return np.array(list(coords.values()))


##### MAIN CLASS DEFINITION  ######

class Platform():
    '''
    The platform class includes all the methods required to control the Dobot
    robotic arm, the Arduino and the Precigenome pressure regulator
    '''
    def __init__(self):
        print('Created platform instance')

        # Define the initial starting conditions
        self.frequency = 20
        self.pulse_width = 3000
        self.refuel_width = 47000

        self.test_droplet_count = 5
        self.chamber_volume = 7.5

    def initiate_all(self):
        self.init_pressure()
        self.init_dobot()
        self.init_ard('COM6')

    def disconnect_all(self):
        platform.disconnect_dobot()
        platform.close_ard()
        platform.close_reg()

    def init_dobot(self):
        '''
        Establishes the connection to the Dobot and sets its movement parameters.
        It also reads in the print calibration file which includes the locations
        of the loading and tube positions.
        '''
        self.api = dType.load()
        self.CON_STR = {
            dType.DobotConnect.DobotConnect_NoError:  "DobotConnect_NoError",
            dType.DobotConnect.DobotConnect_NotFound: "DobotConnect_NotFound",
            dType.DobotConnect.DobotConnect_Occupied: "DobotConnect_Occupied"}

        self.state = dType.ConnectDobot(self.api, "", 115200)[0]
        print("Connect Dobot status:",self.CON_STR[self.state])
        if (self.state != dType.DobotConnect.DobotConnect_NoError):
            print('failed')
            return
        else:
            print('Successful connection')

        dType.SetDeviceName(self.api,'Dobot Magician')
        print(dType.GetDeviceName(self.api)[0])

        #Clean Command Queued
        dType.SetQueuedCmdClear(self.api)

        #Async Motion Params Setting
        dType.SetHOMEParams(self.api, 200, 0, 100, 0, isQueued = 1)
        dType.SetPTPJointParams(self.api, 200, 200, 200, 200, 200, 200, 200, 200, isQueued = 1)
        dType.SetPTPCommonParams(self.api, 100, 100, isQueued = 1)

        self.activate_gripper()
        self.get_plate_data()
        self.current_row = 0
        self.current_column = 0

        self.calibration_file_path = '../Calibrations/print_calibrations.json'
        with open(self.calibration_file_path) as json_file:
            self.calibration_data =  json.load(json_file)
        self.loading_position = self.calibration_data['loading_position']
        self.tube_position = self.calibration_data['tube_position']


        return

    def home_dobot(self):
        '''
        Initially resets the Dobot's position and then initiates the homing
        protocol. Reseting the position ensures that the arm is not extended
        when rotating
        '''
        print("Home Dobot? (y/n)")
        if not ask_yes_no():
            return
        print("Homing...")
        self.reset_dobot_position()
        last_index = dType.SetHOMECmd(self.api, temp = 0, isQueued = 1)
        run_cmd(self.api,last_index)
        return

    def reset_dobot_position(self):
        '''
        Moves the Dobot to a location where its range is limited to avoid
        the arm making contact during homing
        '''
        print("Reset Dobot position? (y/n)")
        if not ask_yes_no():
            return
        self.move_dobot(200,0,150)
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
        self.plate_file_path = '../Calibrations/shallow-384_well_plate.json'
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
        print('Z steps:',self.row_z_step,self.col_z_step)

        self.current_coords = self.top_left
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
        print('get well coords')
        x,y = self.correct_xy_coords(row*self.spacing,column*self.spacing)
        z = self.top_left['z'] + (row * self.row_z_step) + (column * self.col_z_step)
        return {'x':x, 'y':y, 'z':z}

    def change_print_position(self):
        '''
        Initiates a protocol to modify the expected well locations of a given
        plate. Moves from corner to corner allowing the operator to manually
        drive the dobot to correct any deviations. Once all the points are
        corrected, the new positions are stored in the plate metadata file.
        '''
        print("Change print position? (y/n)")
        if not ask_yes_no(): return
        self.move_to_print_position()
        self.dobot_manual_drive()
        self.top_left = self.current_coords

        self.move_dobot(self.top_right['x'], self.top_right['y'], self.top_right['z'])
        self.dobot_manual_drive()
        self.top_right = self.current_coords

        self.move_dobot(self.bottom_right['x'], self.bottom_right['y'], self.bottom_right['z'])
        self.dobot_manual_drive()
        self.bottom_right = self.current_coords

        self.move_dobot(self.bottom_left['x'], self.bottom_left['y'], self.bottom_left['z'])
        self.dobot_manual_drive()
        self.bottom_left = self.current_coords

        self.gen_trans_matrix()

        self.row_z_step = (self.bottom_left['z'] - self.top_left['z']) / (self.max_rows )
        self.col_z_step =  (self.top_right['z'] - self.top_left['z']) / (self.max_columns)

        self.write_plate_data()
        return

    def change_tube_position(self):
        '''
        Changes the position of the calibration tube located in the tube rack
        '''
        print("Change tube position? (y/n)")
        if not ask_yes_no(): return
        self.move_to_tube_position()
        self.dobot_manual_drive()
        self.tube_position = self.current_coords

        self.write_printing_calibrations()
        return

    def write_plate_data(self):
        '''
        Takes all of the current plate data and updates the metadata file
        '''
        print("Store print position? (y/n)")
        if not ask_yes_no(): return
        self.plate_data['top_left'] = self.top_left
        self.plate_data['top_right'] = self.top_right
        self.plate_data['bottom_right'] = self.bottom_right
        self.plate_data['bottom_left'] = self.bottom_left

        print("Write print position to file? (y/n)")
        if not ask_yes_no(): return
        with open(self.plate_file_path, 'w') as outfile:
            json.dump(self.plate_data, outfile)
        print("Plate data saved")

    def write_printing_calibrations(self):
        '''
        Updates the print calibrations json file
        '''
        print("Store print calibrations? (y/n)")
        if not ask_yes_no(): return
        self.calibration_data['loading_position'] = self.loading_position
        self.calibration_data['tube_position'] = self.tube_position

        print("Write print position to file? (y/n)")
        if not ask_yes_no(): return
        with open(self.calibration_file_path, 'w') as outfile:
            json.dump(self.calibration_data, outfile)
        print("Printing calibrations saved")


    def move_to_loading_position(self):
        '''
        Moves the Dobot to the loading position specified in
        printing_calibrations.json
        '''
        print('Moving to loading position...')
        self.move_dobot(self.loading_position['x'],self.loading_position['y'],self.loading_position['z'])
        return

    def move_to_tube_position(self):
        '''
        Moves the Dobot to the tube position specified in
        printing_calibrations.json
        '''
        print('Moving to tube position...')
        self.move_dobot(self.tube_position['x'],self.tube_position['y'],self.tube_position['z'])
        return

    def move_to_print_position(self):
        '''
        Moves the Dobot to well A1 specified in the plate metadata file
        '''
        print('Moving to printing position...')
        self.move_dobot(self.top_left['x'],self.top_left['y'],self.top_left['z'])
        self.current_row = 0
        self.current_column = 0
        return

    def move_dobot(self,x,y,z):
        '''
        Takes a set of XYZ coordinates and moves the Dobot to that location
        '''
        print('Dobot moving...',end='')
        last_index = dType.SetPTPCmd(self.api, dType.PTPMode.PTPMOVLXYZMode, x,y,z,0, isQueued = 1)
        run_cmd(self.api,last_index)
        self.current_coords = {'x':x,'y':y,'z':z}

        print('Current position: x={}\ty={}\tz={}'.format(x,y,z))

        return

    def move_to_well(self,row,column):
        '''
        Moves the Dobot to a defined well while checking that the well is within
        the bounds of the plate
        '''
        if row <= self.max_rows and column <= self.max_columns and row >= 0 and column >= 0:
            target_coords = self.get_well_coords(row,column)
            self.move_dobot(target_coords['x'],target_coords['y'],target_coords['z'])
            self.current_row = row
            self.current_column = column
            return
        else:
            print("Well out of range")
            return

    def activate_gripper(self):
        last_index = dType.SetEndEffectorGripper(self.api,True,False,isQueued=1)
        run_cmd(self.api,last_index)
        return

    def deactivate_gripper(self):
        last_index = dType.SetEndEffectorGripper(self.api,False,False,isQueued=1)
        run_cmd(self.api,last_index)
        return

    def open_gripper(self):
        last_index = dType.SetEndEffectorGripper(self.api,True,False,isQueued=1)
        run_cmd(self.api,last_index)
        print('- Gripper open')
        return

    def close_gripper(self):
        last_index = dType.SetEndEffectorGripper(self.api,True,True,isQueued=1)
        run_cmd(self.api,last_index)
        print('- Gripper closed')
        return

    def load_gripper(self):
        '''
        Initiates a protocol to open and close the gripper to make exchanging
        printer heads easier
        '''
        print('Load gripper? (y/n)')
        if not ask_yes_no(): return
        print('Press enter to open gripper')
        input()
        self.open_gripper()
        print('Press enter to close gripper')
        input()
        self.close_gripper()

    def dobot_manual_drive(self):
        '''
        Initiates the manual drive protocol to control the movement of the
        Dobot using the keyboard. Directs movement in the XYZ
        directions by a defined step size that can be changed to allow for
        coarse or fine grain movement
        '''
        print("starting manual dobot control")
        x = self.current_coords['x']
        y = self.current_coords['y']
        z = self.current_coords['z']
        possible_steps = [0.1,0.5,1,5,10,20]
        step_num = len(possible_steps)*10
        step = possible_steps[abs(step_num) % len(possible_steps)]
        while True:
            try:
                c = msvcrt.getch().decode()
                if c == "w":
                    x -= step
                elif c == "s":
                    x += step
                elif c == "a":
                    y -= step
                elif c == "d":
                    y += step
                elif c == "k":
                    z += step
                elif c == "m":
                    z -= step
                elif c == 'f':
                    step_num = step_num + 1
                    step = possible_steps[abs(step_num) % len(possible_steps)]
                    print('changed to {}'.format(step))
                elif c == 'v':
                    step_num = step_num - 1
                    step = possible_steps[abs(step_num) % len(possible_steps)]
                    print('changed to {}'.format(step))
                elif c == "q":
                    print('Quit (y/n)')
                    if ask_yes_no():
                        return
                    else:
                        print("Didn't quit")
                else:
                    print("not valid")
            except:
                print('not valid')
            # print('Current position: x={}\ty={}\tz={}'.format(self.x,self.y,self.z))
            self.move_dobot(x,y,z)

    def drive_platform(self):
        '''
        Comprehensive manually driving function. Within this method, the
        operator is able to move the dobot by wells, load and unload the
        gripper, set and control pressures, and print defined arrays
        '''
        print("Driving platform...")
        while True:
            try:
                c = msvcrt.getch().decode()
                print(c)
                if c == "w":
                    self.move_to_well(self.current_row - 1, self.current_column)
                elif c == "s":
                    self.move_to_well(self.current_row + 1, self.current_column)
                elif c == "a":
                    self.move_to_well(self.current_row, self.current_column - 1 )
                elif c == "d":
                    self.move_to_well(self.current_row, self.current_column + 1)
                elif c == 'g':
                    self.load_gripper()
                elif c == 'p':
                    self.move_to_print_position()
                elif c == 'l':
                    self.move_to_loading_position()
                elif c == '[':
                    self.move_to_tube_position()
                elif c == 'y':
                    self.change_print_position()
                elif c == 'h':
                    self.change_tube_position()
                elif c == 't':
                    self.print_droplets(20,3000,50000,10)
                elif c == 'o':
                    self.pressure_on()
                elif c == 'i':
                    self.pressure_off()
                elif c == 'u':
                    self.set_pressure(10,10)
                elif c == 'x':
                    self.refuel_test()
                elif c == 'c':
                    self.pulse_test()
                elif c == ']':
                    self.move_dobot(self.top_right['x'], self.top_right['y'], self.top_right['z'])
                elif c == ';':
                    self.move_dobot(self.bottom_left['x'], self.bottom_left['y'], self.bottom_left['z'])
                elif c == '.':
                    self.move_dobot(self.bottom_right['x'], self.bottom_right['y'], self.bottom_right['z'])

                elif c == '1':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.01)
                elif c == '2':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.1)
                elif c == '3':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.1)
                elif c == '4':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.01)

                elif c == '6':
                    self.set_pressure(self.pulse_pressure - 0.01,self.refuel_pressure)
                elif c == '7':
                    self.set_pressure(self.pulse_pressure - 0.1,self.refuel_pressure)
                elif c == '8':
                    self.set_pressure(self.pulse_pressure + 0.1,self.refuel_pressure)
                elif c == '9':
                    self.set_pressure(self.pulse_pressure + 0.01,self.refuel_pressure)

                elif c == "q":
                    print('Quit (y/n)')
                    if ask_yes_no():
                        return
                    else:
                        print("Didn't quit")
                else:
                    print("not valid")
            except:
                print("Unable to complete action")

    def disconnect_dobot(self):
        self.deactivate_gripper()
        dType.DisconnectDobot(self.api)
        return

    def init_ard(self,port):
        print('Initizing arduino...')
        self.ser = serial.Serial(port=port, baudrate=115200, bytesize=8, parity='N', stopbits=1, xonxoff=0, timeout=0)
        time.sleep(1)
        return

    def print_droplets(self,freq,pulse_width,refuel_width,count):
        '''
        Sends the desired printing instructions to the Arduino
        '''
        print('starting print...',end='')
        self.ser.write(SetParam_CtrlSeq(freq,pulse_width,refuel_width,count))
        time.sleep(0.2)
        self.ser.write(Switch_CtrlSeq(1))
        time.sleep(0.2)

        current = self.ser.read().decode()
        while current != 'C':
            current = self.ser.read().decode()
            time.sleep(0.1)

        time.sleep(0.1)
        print('print complete')
        return

    def refuel_test(self):
        '''
        Defined printing protocol used in calibration
        '''
        print('Refuel test')
        print(self.frequency,0,self.refuel_width,self.test_droplet_count)
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
        self.ser.close()
        return

    def init_pressure(self):
        '''
        Initiates the Precigenome pressure regulator and the two different
        channels used
        '''
        print("Connecting pressure regulator...")
        self.mcfs = PGMFC()
        self.mcfs.monitor_start(span=100)
        time.sleep(1)
        self.channel_pulse = self.mcfs[1]
        self.channel_refuel = self.mcfs[2]
        print('Successful connection')

        self.set_pressure(2, 0.3)
        return

    def set_pressure(self,pulse,refuel,runtime=600):
        self.pulse_pressure = pulse
        self.refuel_pressure = refuel

        self.channel_pulse.set_params(peak=pulse,runtime=runtime)
        self.channel_refuel.set_params(peak=refuel,runtime=runtime)
        print("Pulse={}\tRefuel={}".format(pulse,refuel))
        return

    def pulse_on(self):
        self.channel_pulse.purge_on()
        return

    def refuel_on(self):
        self.channel_refuel.purge_on()
        return

    def pulse_off(self):
        self.channel_pulse.purge_off()
        return

    def refuel_off(self):
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
        self.mcfs.close()
        return

    def calc_resistance(self,counter,droplets,width,pressure,volume):
        '''
        Utilizes the equation defined in the printing_calibration_methods.md
        file
        '''
        return (counter * droplets * (width * 10**-3) * (6874.76 * pressure)) / (volume * 10**-9)

    def resistance_testing(self):
        '''
        Directs the operator through the calibration process that is defined in
        the printing_calibration_methods.md file
        '''
        print('Resistance testing mode...')
        print('Current overflow chamber volume: ',self.chamber_volume)
        print('Prepare chip for testing')
        click_counter = 0
        step = 'start'
        refuel_counter = 0
        pulse_counter = 0
        refuel_resistances = []
        pulse_resistances = []

        refuel_times = []
        pulse_times = []

        valid = True

        while True:
            try:
                c = msvcrt.getch().decode()
                valid = True
            except:
                print('Not a valid input')
                valid = False
            if valid:
                print(c)
                if c == "x":
                    if step == 'refuel' or step == 'start':
                        self.refuel_test()
                        click_counter += 1
                elif c == "c":
                    if step == 'pulse' or step == 'start':
                        self.pulse_test()
                        click_counter += 1
                elif c == 'z':
                    if step == 'start':
                        step = "refuel"
                    elif step == 'refuel':
                        resistance = calc_resistance(click_counter, self.test_droplet_count,self.refuel_width,self.refuel_pressure,self.chamber_volume)
                        refuel_resistances.append(round((resistance * 10**-11),2))
                        refuel_times.append(click_counter * self.test_droplet_count * self.refuel_width)
                        refuel_counter += 1
                        step = 'pulse'
                        print('Calculated resistance = ',resistance)
                    else:
                        resistance = calc_resistance(click_counter, self.test_droplet_count,self.pulse_width,self.pulse_pressure,self.chamber_volume)
                        pulse_resistances.append(round((resistance * 10**-11),2))
                        pulse_times.append(click_counter * self.test_droplet_count * self.pulse_width)
                        pulse_counter += 1
                        step = 'refuel'
                        print('Calculated resistance = ',resistance)
                    print('Currently on {}\trefuel counter = {}\tpulse counter = {}'.format(step,refuel_counter,pulse_counter))

                elif c == 'o':
                    self.pressure_on()
                elif c == 'i':
                    self.pressure_off()
                elif c == 'u':
                    self.set_pressure(10, 10)
                elif c == 'j':
                    self.set_pressure(2, 0.3)

                elif c == '1':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.01)
                elif c == '2':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure - 0.1)
                elif c == '3':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.1)
                elif c == '4':
                    self.set_pressure(self.pulse_pressure,self.refuel_pressure + 0.01)

                elif c == '6':
                    self.set_pressure(self.pulse_pressure - 0.01,self.refuel_pressure)
                elif c == '7':
                    self.set_pressure(self.pulse_pressure - 0.1,self.refuel_pressure)
                elif c == '8':
                    self.set_pressure(self.pulse_pressure + 0.1,self.refuel_pressure)
                elif c == '9':
                    self.set_pressure(self.pulse_pressure + 0.01,self.refuel_pressure)

                elif c == "q":
                    print('Quit resistance testing mode? (y/n)')
                    if ask_yes_no():
                        return
                    else:
                        print("Didn't quit")
                else:
                    print("Not a valid input")
            if pulse_counter == 3:
                print('Refuel resistances:\t{}\t{}\t{}'.format(refuel_resistances[0],refuel_resistances[1],refuel_resistances[2]))
                print('Pulse resistances:\t{}\t{}\t{}'.format(pulse_resistances[0],pulse_resistances[1],pulse_resistances[2]))
                print('Refuel times:\t{}\t{}\t{}'.format(refuel_times[0],refuel_times[1],refuel_times[2]))
                print('Pulse times:\t{}\t{}\t{}'.format(pulse_times[0],pulse_times[1],pulse_times[2]))
                print('\nAverages:')
                print('Resistances:\tRefuel = {}\tPulse = {}'.format(round(np.mean(refuel_resistances),2),round(np.mean(pulse_resistances),2)))
                print('Times:\tRefuel = {}\tPulse = {}'.format(round(np.sum(refuel_times),2),round(np.mean(pulse_times),2)))
                return
