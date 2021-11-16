from Precigenome.PGMFC import PGMFC
import time
from utils import *


class Regulator:
    def __init__(self,sim):
        print('started reg')


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
        self.pressure_on()
        return

    def set_pressure(self,pulse,refuel,runtime=6000):
        self.pulse_pressure = pulse
        self.refuel_pressure = refuel
        if not self.sim:
            self.channel_pulse.set_params(peak=pulse,runtime=runtime)
            self.channel_refuel.set_params(peak=refuel,runtime=runtime)
        print("Setting pressure: Pulse={}\tRefuel={}".format(pulse,refuel))
        return

    def update_pressure(self,verbose=True):
        if not self.sim:
            pulse = self.channel_pulse.get_pressure()[0]
            refuel = self.channel_refuel.get_pressure()[0]
            self.real_pulse =  pulse
            self.real_refuel = refuel
        else:
            pulse = self.pulse_pressure
            refuel = self.refuel_pressure
        if verbose:
            print("Current pressure: Pulse={}\tRefuel={}".format(round(pulse,2),round(refuel,2)))
        return

    def check_pressures(self,tolerance=0.1,verbose=False):
        if self.sim:
            print('No pressure check in Sim')
            return

        self.update_pressure(verbose=verbose)
        refuel_diff = np.abs((self.real_refuel - self.refuel_pressure) / self.refuel_pressure)
        pulse_diff = np.abs((self.real_pulse - self.pulse_pressure) / self.pulse_pressure)

        if refuel_diff =< 0.1 and pulse_diff =< 0.1:
            print(f'Pressures within tolerance {tolerance}')
            self.correct_pressure = True
        else:
            self.correct_pressure = False
            if verbose:
                print(f'Pressures are incorrect: Refuel: {refuel_diff} Print: {pulse_diff}')
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
