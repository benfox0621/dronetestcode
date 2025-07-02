import sys
import time
import logging

from NatNetClient import NatNetClient
import rclpy
from rclpy import node
from std_msgs.msg import String


import DataDescriptions
import MoCapData
import threading
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.mem import MemoryElement
from cflib.crazyflie.mem import Poly4D
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from cflib.utils.reset_estimator import reset_estimator
from cflib.positioning.motion_commander import  MotionCommander
from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger


# set drones URI (address for radio)
uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

# set global pos and rot variables, then lock position for threading security
latest_position = None
latest_rotation = None
position_lock = threading.Lock()


# rigid body listener callback, assigns global variable "latest_position" as the newest frame data for position, and same for rotation
def rrbf(new_id, position, rotation):
    global latest_position
    global latest_rotation
    latest_rotation = rotation
    latest_position = position
    #print(f'heard position to be {position}')
   

    


# full motion capture setup and control, including data send to crazyflie. 
# cf is an argument so that the crazyflie connection is called in __main__ once to conserve resources. 
# you MUST use the with crazyflie as ... in __main__ or this will not recognize cf as a valid argument
def mocap_thread(cf):
    local_ip="10.131.220.228"
    server_ip="10.131.206.160"
    streaming_client = NatNetClient()
    streaming_client.set_use_multicast(False)
    streaming_client.set_client_address(local_ip)
    streaming_client.set_server_address(server_ip)
    streaming_client.rigid_body_listener = rrbf
    streaming_client.set_print_level(0)     
    # set print level 0 prints only frame data but i commented out the print statement in natnetclient.py
    # this has not caused any noticeable issues and to keep the terminal less cluttered i would recommend keeping it this way.
    

    if streaming_client.run('d'):
        print("Connection thread started")

        # Wait for actual connection to complete
        import time
        time.sleep(3)

        if streaming_client.connected():
            print("Connected to Motive server!")
            # repeat data send 1000 times with a interval set between sends, currently set to 0.02 seconds, thus 50hz and 20 total seconds of data.
            for _ in range(1000):
                with position_lock:

                    # if position variables are non-empty
                    if latest_position and latest_rotation:

                        # Extract position
                        if isinstance(latest_position, (tuple, list)):
                            x, y, z = latest_position
                        else:
                            x, y, z = latest_position.x, latest_position.y, latest_position.z

                        # Extract rotation quaternion
                        if isinstance(latest_rotation, (tuple, list)):
                            qx, qy, qz, qw = latest_rotation
                        else:
                            qx, qy, qz, qw = (latest_rotation.x, latest_rotation.y, latest_rotation.z, latest_rotation.w)

                        # send full pose including rotation, optionally you can send just position with cf.extpos.send_extpos(x,y,z) <--- note the "e" missing at the end of send_extpos
                        cf.extpos.send_extpose(x, y, z, qx, qy, qz, qw)
                        #print(f"Sending extpos: x={x:.2f}, y={y:.2f}, z={z:.2f}, qx={qx:.2f}, qy={qy:.2f}, qz={qz:.2f}, qw={qw:.2f}")
                    else:
                        print("Waiting for position data...")
                time.sleep(0.02)  # 50 Hz update rate
        else:
            print("Not connected. Check IP and firewall.")
            # if this error happens check that the optitrack machine is NOT on loopback mode in the stream settings. 
            # additionally ensure that the windows PC is on EDUROAM or the IP will be wrong or not connect at all.
            # idk if IP addresses change with updates but if the script doesnt work right, consider checking the IP in windows settings -> network -> wifi settings/properties or whatever the path is
    else:
        print("Failed to start client run loop")
 

    try:
        while True:
            key = input()
            if key.lower().strip() == 'q':
                break
    except KeyboardInterrupt:
        pass
    finally:
        streaming_client.shutdown()
        print("shutting down")

        # honestly that code doesnt do anything to affect the drone flight, stopping mocap would likely do nothing if the drone is going crazy.

def drone_control_thread(cf):
    global latest_position
    
    
    print("Connected to Crazyflie")

    print('attempting to arm cf')

    # you MUST arm the crazyflie to use it
    cf.platform.send_arming_request(True)
    print("crazyflie armed")
    
    # reset position estimator and give it 10 seconds
    time.sleep(1.0)
    orientation_std_dev = 8.0e-3
    time.sleep(1.0)
    reset_estimator(cf)
    time.sleep(10)
    cf.param.set_value('stabilizer.estimator', '2')
    
   
    print('values set')

    # actually control the drone now
    # make sure to give a decent bit of time between commands or they will all run at the exact same time, which will either do nothing or make the drone crash idk which
    
    commander = cf.high_level_commander
    time.sleep(2)
    print("taking off")
    
    commander.takeoff(0.5,0.5)
    time.sleep(5)  # Give time to start takeoff

    commander.go_to(0.5, 0.5, 0.5, 0, 5)
    time.sleep(5)

    commander.land(0.0, 0.5)
    time.sleep(3.0)

    commander.stop() 

# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def log_stab_callback(timestamp, data, logconf):
    print('[%d][%s]: %s' % (timestamp, logconf.name, data))

def simple_log_async(scf, logconf):
    cf = scf.cf
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()
    time.sleep(100)
    logconf.stop()
    
 
if __name__ == '__main__':
    cflib.crtp.init_drivers()
   
   # set up logging
    lg_trgt = LogConfig(name='Stabilizer',period_in_ms=100)
    lg_trgt.add_variable('ctrltarget.z','float')

    # connect to crazyflie and run threads
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf=scf.cf
        uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
        print(uri)
        
        # comma is after the arg so that it reads as a string. if it had no comma, each letter of the string will read as an argument and you will get errors.
        x = threading.Thread(target=drone_control_thread, args=(cf,))
    
        y = threading.Thread(target=mocap_thread, args=(cf,))
        z = threading.Thread(target=simple_log_async, args=(scf, lg_trgt,))
        # Start the Crazyflie control thread
        x.start()
        
        # Start the MoCap data thread
        y.start()
        z.start()


        try:
            while True:
                time.sleep(1)  # Main thread can also handle user input or perform other tasks
        except KeyboardInterrupt:
            print("Shutting down program...")