import sys
import time
import threading
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from cflib.utils.reset_estimator import reset_estimator
from cflib.positioning.motion_commander import  MotionCommander
from library import functions

controller = functions.control()

if __name__ == '__main__':

    cflib.crtp.init_drivers()

    local_ip = "10.131.220.228"
    server_ip = input("What is the server ip?")
    
    uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf
        
        controller.init_drone(cf)

        if server_ip:
            mocap = threading.Thread(target=controller.mocap_listener, args=(local_ip, cf, server_ip,))
        else: 
            mocap = threading.Thread(target=controller.mocap_listener, args=(local_ip, cf,))

        takeoff = threading.Thread(target=controller.takeoff, args=(cf,))
        mocap.start()


        time.sleep(2)
        takeoff.start()