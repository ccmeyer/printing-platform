#from enum import Enum
from __future__ import annotations
from abc import ABC, abstractmethod
import time
from Precigenome.PGMFC import PGMFC
mfcs = PGMFC()

class Wrapper:
    def __init__(self):
        pass

class PressureCtrlWrapperImpl(ABC):
    _implType=0
    _channelToPressure=0
    # add more variables here! 
    # make them protected by adding prefix "_"
    def __init__(self):
#        self.ImplType=0
#        self.ChannelToPressure=dict()
        pass
    def connect(self):
        pass
    def setPressure(self, airpressure, airchannel):
        pass
    def purgeOn(self, airchannel):
        pass
    def purgeOff(self, airchannel):
        pass
    def readPressure(self, airchannel)->float:
        pass
    # add more interfac function here!

class PressureCtrlWrapperImplPreci(PressureCtrlWrapperImpl):
    def __init__(self):
        super().__init__()
        self._implType=1
        self._channelToPressure=dict()
    def connect(self):
        print("Connected to Pressure Ctrl...")
        print(mfcs)
        mfcs.monitor_start(span=100)
    def setPressure(self, airchannel, airpressure):
        print("Set pressure...")
        self._channelToPressure.update({airchannel:airpressure})
        mfcs.set_params(channel=airchannel, peak=airpressure, runtime=600)
    def purgeOn(self, airchannel):
        print("Start running...")
        mfcs.purge_on(airchannel)
    def purgeOff(self, airchannel):
        print("Stop running...")
        mfcs.purge_off(airchannel)
    def readPressure(self, airchannel)->float:
        print("Get pressure...")
        print(mfcs.get_pressure(airchannel))
        return self._channelToPressure.get(airchannel) 
    # add more function implementation here!

#class PressureCtrlWrapper(Enum):
class PressureCtrlWrapper(Wrapper):
#   PRECI=1
    _impl=0
    def __init__(self, eImplType):
        if eImplType==1:
            self._impl=PressureCtrlWrapperImplPreci()
        else:
            self._impl=PressureCtrlWrapperImplPreci() #default implementation
# switcher={
#         1:PressureCtrlWrapperImplPreci
# }
# self.Impl=switcher.get(PRECI,PressureCtrlWrapperImplPreci) """
    def connect(self):
        self._impl.connect()
    def setPressure(self, airchannel, airpressure):
        self._impl.setPressure(airchannel, airpressure)
    def purgeOn(self, airchannel):
        self._impl.purgeOn(airchannel)
    def purgeOff(self, airchannel):
        self._impl.purgeOff(airchannel)
    def readPressure(self,airchannel)->float:
        return self._impl.readPressure(airchannel)


def test_code() -> None:
    rWrpper=PressureCtrlWrapper(1)
    rWrpper.connect()
    rWrpper.setPressure(1, 10)
    rWrpper.setPressure(2, 10)
    rWrpper.purgeOn(1)
    rWrpper.purgeOn(2)
    time.sleep(10)
    rWrpper.readPressure(1)
    rWrpper.readPressure(2)
    time.sleep(10)
    rWrpper.purgeOff(1)
    rWrpper.purgeOff(2)

if __name__ == "__main__":
    test_code()
    
