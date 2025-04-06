from gpiozero import Button
from signal import pause
import time
from PyQt5.QtCore import QTimer, QThread
#print(dir(Button))
def onButtonPress():
    print("Pressed")
    return 1
class SquidButton():
    def __init__(self,pin,cooldown):
        self.button=Button(pin)
        self.alreadyPressed=False
        self.timerStart=time.time()
        self.timer=0
        self.timerLength=cooldown
        self.button.when_pressed=self.button_pressed
    def button_pressed(self):
        if((self.alreadyPressed is False) and (self.button.is_pressed is True)):
            onButtonPress()
            self.alreadyPressed=True
            self.timerStart=time.time()
            self.timer=self.timerLength-(time.time()-self.timerStart)
        elif self.timer>0:
            self.timer=self.timerLength-(time.time()-self.timerStart)
            print(self.timer)
            if self.timer<=0:
                self.endCoolDown()
    def endCoolDown(self):
        self.alreadyPressed=False
        print("cooldown over")

button=SquidButton(25,5)
print("Program started")
pause()
