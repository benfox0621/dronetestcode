import sys
import time
try:
    from motive2ros.library.NatNetClient import NatNetClient  # or whatever module you're using
except ImportError:
    print("Please download the NatNet SDK and place the Python client in the proper directory.")
    exit(1)

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Pose, Point, Quaternion


import threading
import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.mem import MemoryElement
from cflib.crazyflie.mem import Poly4D
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from cflib.utils.reset_estimator import reset_estimator
from cflib.positioning.motion_commander import  MotionCommander

newpos = None
newrot = None

lock = threading.Lock()

class control():
    def rrbf(self, new_id, position, rotation):
        global newpos
        global newrot
    
        newpos = position
        newrot = rotation

    def mocap_listener(self, local_ip, cf: Crazyflie, server_ip: str = '10.131.196.172'):
        global newpos
        global newrot
        # local_ip and server_ip should be used as strings

        client = NatNetClient()
        client.set_use_multicast(False)
        client.set_client_address(local_ip)
        client.set_server_address(server_ip)
        client.rigid_body_listener = self.rrbf
        client.set_print_level(0)
        
        while True:
            client.run('d')

            time.sleep(1)
            if client.connected():
                print("Connected to server")
                break
            else:
                print("Not connected")
        
        while True:
            with lock:
                if newpos is not None and newrot is not None:
                    x, y, z = newpos
                    qx, qy, qz, qw = newrot
                    cf.extpos.send_extpose(x, y, z, qx, qy, qz, qw)
                    print(f"Sending extpos: x={x:.2f}, y={y:.2f}, z={z:.2f}")
                time.sleep(0.1)

                    # 10hz data send rate

    def init_drone(self, cf: Crazyflie):
        
        cf.platform.send_arming_request(True)
        print("Crazyflie armed")
        cf.param.set_value('stabilizer.estimator', '2')
        print('values set')
       

    def takeoff(self, cf: Crazyflie):
        global newpos
        global newrot
        commander = cf.high_level_commander

        commander.takeoff(0.5, 5)
        time.sleep(5)
        commander.stop()
        # this part doesnt work ^^^ the stop function doesnt do anything for some reason, need to investigate further

        # while newpos is None or newrot is None:
        #     time.sleep(1)
        #     print("Waiting for pose data")
        # for _ in range(100):
        #     print("this would be a takeoff attempt")
        #     time.sleep(0.1)

class mocap_basic_pub(Node):
    def __init__(self, group, local, server):
        #initialize the ip addresses 
        
        self.localip = local
        self.serverip = server
        self.groupid = group
        
    
        
        self.counter = 0
        self.client = NatNetClient()
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', group)


        self.mocap_init()
        self.running = True
      
    def rrbf(self, new_id, position, rotation):
        
        if not rclpy.ok():
            return
        # Format as "id;x,y,z;qx,qy,qz,qw"
        pos_str = ",".join(f"{x:.3f}" for x in position)
        rot_str = ",".join(f"{x:.4f}" for x in rotation)
        msg_str = f"{new_id};{pos_str};{rot_str}"
        msg = String()
        msg.data = msg_str

        print(f"Publishing ID {new_id}: {msg.data}")  # DEBUG

        try:
            self.publisher_.publish(msg)
        except Exception as e:
            self.get_logger().warn(f"Publish failed: {e}")
            return

        
        self.counter += 1
        
        if self.counter % 10 == 0:
            pass
            #print(f"\rFrame {self.counter} Time {time:.2f}", end='', flush=True)
            #self.get_logger().info(f"\rFrame {self.counter} Time {time} Position: {self.position.x}, {self.position.y}, {self.position.z}", end='',flush=True)

    def mocap_init(self):

        # init mocap
        
        self.client.set_use_multicast(False)
        self.client.set_client_address(self.localip)
        self.client.set_server_address(self.serverip)
        self.client.rigid_body_listener = self.rrbf
        self.client.set_print_level(0)

        # connect loop until it connects
        while True:
            self.client.run('d')

            time.sleep(1)
            if self.client.connected():
                
                break
            else:
                print("Not connected")
    
    def destroy_node(self):
        self.running = False
        self.client.shutdown()
        super().destroy_node()
                
class mocap_basic_sub(Node):
    
    def __init__(self, group):
        self.groupid = group
        
        
        
        super().__init__('minimal_subscriber')
        self.declare_parameter('id', 0)
        id_param = self.get_parameter('id').get_parameter_value().integer_value
        self.streamid = str(id_param)
        self.subscription = self.create_subscription(String, 'topic', self.listener_callback, group)

    def listener_callback(self, msg):
        data = msg.data  # e.g. "5;1.234,2.345,3.456;0.0000,0.0000,0.0000,1.0000"
        
        # Split the string by ';' into parts: [id, position_str, rotation_str]
        parts = data.split(';')
        if len(parts) != 3:
            self.get_logger().warning(f"Unexpected data format: {data}")
            return
        
        received_id = parts[0]
        position_str = parts[1]  # e.g. "1.234,2.345,3.456"
        rotation_str = parts[2]  # e.g. "0.0000,0.0000,0.0000,1.0000"

        if received_id == self.streamid:
            # Further split position and rotation by ','
            position = [float(x) for x in position_str.split(',')]  # [1.234, 2.345, 3.456]
            rotation = [float(x) for x in rotation_str.split(',')]  # [0.0, 0.0, 0.0, 1.0]
        
            # Now you can use received_id, position, and rotation as needed
        
            print(f"ID: {received_id}")
            print(f"Position: {position}")
            print(f"Rotation: {rotation}")

class complete_node_pub(mocap_basic_pub):
    def __init__(self, group = 10, local = "10.131.220.228", server = "10.131.196.172"):
        rclpy.init()

        publisher = mocap_basic_pub(group, local, server)
        try: 
            rclpy.spin(publisher)
        except KeyboardInterrupt:
            pass
        finally:
            publisher.destroy_node()

            rclpy.shutdown()

class complete_node_sub(mocap_basic_sub):
    def __init__(self, group = 10):
        rclpy.init()
        
        
        subscriber = mocap_basic_sub(group)
        try: 
            rclpy.spin(subscriber)
        except KeyboardInterrupt:
            pass
        finally:
            subscriber.destroy_node()

            rclpy.shutdown()
