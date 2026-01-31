from picoed import button_b, button_a
from time import sleep

from senzory import Senzory

if __name__ == "__main__":
    senzory = Senzory
    while not button_a.was_pressed():
        
        data = senzory.vycti()
        print(data)
        sleep(0.1)        
