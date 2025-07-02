import logging
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie

from cflib.crazyflie.log import LogConfig
from cflib.crazyflie.syncLogger import SyncLogger

# URI to the Crazyflie to connect to
uri = 'radio://0/80/2M/E7E7E7E7E7'
# Only output errors from the logging framework
logging.basicConfig(level=logging.ERROR)

def log_stab_callback(timestamp, data, logconf):
    print('[%d][%s]: %s' % (timestamp, logconf.name, data))

def simple_log_async(scf, logconf):
    cf = scf.cf
    cf.log.add_config(logconf)
    logconf.data_received_cb.add_callback(log_stab_callback)
    logconf.start()
    time.sleep(5)
    logconf.stop()

def simple_log(scf, logconf):

    with SyncLogger(scf, logconf) as logger:

        for log_entry in logger:

            timestamp = log_entry[0]
            data = log_entry[1]
            logconf_name = log_entry[2]

            print('[%d][%s]: %s' % (timestamp, logconf_name, data))

            break

def simple_connect():

    print("Yeah, I'm connected! :D")
    time.sleep(3)
    print("Now I will disconnect :'(")

if __name__ == '__main__':
    # Initialize the low-level drivers
    cflib.crtp.init_drivers()

    lg_stab = LogConfig(name='Stabilizer', period_in_ms=10)
    lg_stab.add_variable('stabilizer.roll', 'float')
    lg_stab.add_variable('stabilizer.pitch', 'float')
    lg_stab.add_variable('stabilizer.yaw', 'float')

    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:

        # simple_connect()
        simple_log_async(scf, lg_stab)

# import sys
# import time

# from NatNetClient import NatNetClient
# import rclpy
# from rclpy import node
# from std_msgs.msg import String


# import DataDescriptions
# import MoCapData
# import threading
# import cflib.crtp
# from cflib.crazyflie import Crazyflie
# from cflib.crazyflie.mem import MemoryElement
# from cflib.crazyflie.mem import Poly4D
# from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
# from cflib.utils import uri_helper
# from cflib.utils.reset_estimator import reset_estimator, _wait_for_position_estimator
# from cflib.positioning.motion_commander import  MotionCommander

# uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

# latest_position = None
# latest_rotation = None
# position_lock = threading.Lock()

# def rrbf(new_id, position, rotation):
#     global latest_position
#     global latest_rotation
#     latest_rotation = rotation
#     latest_position = position
   

# def mocap_thread():
#     local_ip="10.131.220.228"
#     server_ip="10.131.206.160"
#     streaming_client = NatNetClient()
#     streaming_client.set_use_multicast(False)
#     streaming_client.set_client_address(local_ip)
#     streaming_client.set_server_address(server_ip)
#     streaming_client.rigid_body_listener = rrbf
#     streaming_client.set_print_level(0)     

    

#     if streaming_client.run('d'):
#         print("Connection thread started")

#         # Wait for actual connection to complete
#         import time
#         time.sleep(1)

#         if streaming_client.connected():
#             print("Connected to Motive server!")
#         else:
#             print("Not connected. Check IP and firewall.")
#     else:
#         print("Failed to start client run loop")
 

#     try:
#         while True:
#             key = input()
#             if key.lower().strip() == 'q':
#                 break
#     except KeyboardInterrupt:
#         pass
#     finally:
#         streaming_client.shutdown()
#         print("shutting down")

# def send_extpos_loop(cf):
#     print("Starting extpos update loop...")
#     try:
#         while True:
#             with position_lock:
#                 if latest_position and latest_rotation:
#                     # Extract position
#                     if isinstance(latest_position, (tuple, list)):
#                         x, y, z = latest_position
#                     else:
#                         x, y, z = latest_position.x, latest_position.y, latest_position.z

#                     if x == 0.0 and y == 0.0 and z == 0.0:
#                         continue

#                     # Extract rotation quaternion
#                     if isinstance(latest_rotation, (tuple, list)):
#                         qx, qy, qz, qw = latest_rotation
#                     else:
#                         qx, qy, qz, qw = latest_rotation.x, latest_rotation.y, latest_rotation.z, latest_rotation.w

#                     cf.extpos.send_extpose(x, z, y, qx, qy, qz, qw)
#             time.sleep(0.02) 
#     except Exception as e:
#         print(f"Extpos thread exception: {e}")


# def drone_control_thread(uri):
#     global latest_position

#     cflib.crtp.init_drivers()
   

 
#     with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
#         print("Connected to Crazyflie")
#         cf=scf.cf
#         print('attempting to arm cf')
#         cf.platform.send_arming_request(True)
#         print("crazyflie armed")
      
#         time.sleep(1.0)
#         orientation_std_dev = 8.0e-3
#         time.sleep(1.0)
      
#         cf.param.set_value('locSrv.extQuatStdDev', orientation_std_dev)
#         cf.param.set_value('stabilizer.estimator', '2')
#         time.sleep(0.5)
#         print('values set')
      
#         # Start the extpos loop in a background thread
#         extpos_thread = threading.Thread(target=send_extpos_loop, args=(cf,), daemon=True)
#         extpos_thread.start()

#         # _wait_for_position_estimator(cf)
#         # reset_estimator(cf)
#         time.sleep(0.5)

       
#         mc = MotionCommander(scf, default_height=0.3)
#         mc.take_off(0.15)
#         time.sleep(2.0)
#         mc.land(0.1)
#         mc.stop()




    
 
# if __name__ == '__main__':
#     uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
#     print(uri)
#     x = threading.Thread(target=drone_control_thread, args=(uri,))
   
#     y = threading.Thread(target=mocap_thread)


#      # Start the MoCap data thread
#     print("starting mocap")
#     y.start()

#     print("sleeping")
#     time.sleep(5)

#     print("sleep done, starting drone")

#     # Start the Crazyflie control thread
#     x.start()


#     try:
#         while True:
#             time.sleep(1)  # Main thread can also handle user input or perform other tasks
#     except KeyboardInterrupt:
#         print("Shutting down program...")