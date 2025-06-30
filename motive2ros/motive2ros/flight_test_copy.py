import sys
import time

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

uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

latest_position = None
latest_rotation = None
position_lock = threading.Lock()

def rrbf(new_id, position, rotation):
    global latest_position
    global latest_rotation
    latest_rotation = rotation
    latest_position = position
   

    



def mocap_thread():
    local_ip="10.131.220.228"
    server_ip="10.131.196.172"
    streaming_client = NatNetClient()
    streaming_client.set_use_multicast(False)
    streaming_client.set_client_address(local_ip)
    streaming_client.set_server_address(server_ip)
    streaming_client.rigid_body_listener = rrbf
    streaming_client.set_print_level(0)     

    

    if streaming_client.run('d'):
        print("Connection thread started")

        # Wait for actual connection to complete
        import time
        time.sleep(1)

        if streaming_client.connected():
            print("Connected to Motive server!")
        else:
            print("Not connected. Check IP and firewall.")
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

def drone_control_thread(uri):
    global latest_position

    cflib.crtp.init_drivers()
   

 
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        print("Connected to Crazyflie")
        cf=scf.cf
        print('attempting to arm cf')
        cf.platform.send_arming_request(True)
        print("crazyflie armed")
      
        time.sleep(1.0)
        orientation_std_dev = 4.5e-3
        time.sleep(1.0)
      
        cf.param.set_value('locSrv.extQuatStdDev', orientation_std_dev)
        cf.param.set_value('stabilizer.estimator', '2')
        print('values set')
      
        commander = cf.high_level_commander

        commander.takeoff(0.5, 1.0)
        time.sleep(1.5)  # Give time to start takeoff
        for _ in range(100):
            with position_lock:
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

                    cf.extpos.send_extpose(x, z, y, qx, qy, qz, qw)
                    print(f"Sending extpos: x={x:.2f}, y={y:.2f}, z={z:.2f}, qx={qx:.2f}, qy={qy:.2f}, qz={qz:.2f}, qw={qw:.2f}")
                else:
                    print("Waiting for position data...")
            time.sleep(0.1)  # 10 Hz update rate

        commander.land(0.0, 1.0)
        time.sleep(3.0)
        commander.stop()
           




    
 
if __name__ == '__main__':
    uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
    print(uri)
    x = threading.Thread(target=drone_control_thread, args=(uri,))
   
    y = threading.Thread(target=mocap_thread)
    # Start the Crazyflie control thread
    x.start()
     # Start the MoCap data thread
    y.start()


    try:
        while True:
            time.sleep(1)  # Main thread can also handle user input or perform other tasks
    except KeyboardInterrupt:
        print("Shutting down program...")