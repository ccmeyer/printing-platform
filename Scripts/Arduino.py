import time
import serial
from utils import *

class Arduino:
    def __init__(self,sim):
        print('started Arduino')


    def init_ard(self,port):
        print('\nInitizing arduino...')
        if not self.sim:
            self.ser = serial.Serial(port=port, baudrate=115200, bytesize=8, parity='N', stopbits=1, xonxoff=0, timeout=0)
            time.sleep(1)
        print('Arduino is connected')
        return

    def SetParam_CtrlSeq(self,feq,pw,repw,pc):  # frequency, pulsewidth and pulsecount
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

    def Switch_CtrlSeq(self,state):
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

    def print_command(self,freq,pulse_width,refuel_width,count):
        self.ser.write(self.SetParam_CtrlSeq(freq,pulse_width,refuel_width,count))
        time.sleep(0.2)
        self.ser.write(self.Switch_CtrlSeq('close'))
        return

    def read_ard(self):
        val = self.ser.readall().decode()
        print('Ard output:',val)
        return val

    def refuel_open(self):
        if not self.ask_yes_no(message='Open refuel valve? (y/n)'):
            print('Quitting...')
            section_break()
            return
        if not self.sim: self.ser.write(self.Switch_CtrlSeq('refuel'))
        return

    def pulse_open(self):
        if not self.ask_yes_no(message='Open printing valve? (y/n)'):
            print('Quitting...')
            section_break()
            return
        if not self.sim: self.ser.write(self.Switch_CtrlSeq('pulse'))
        return

    def close_valves(self):
        if not self.sim: self.ser.write(Sself.witch_CtrlSeq('close'))
        return

    def close_ard(self):
        if not self.sim:
            self.ser.close()
        print('Disconnected Arduino')
        return
