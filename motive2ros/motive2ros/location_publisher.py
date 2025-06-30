import sys
import time

import rclpy 
from rclpy.node import Node

from std_msgs.msg import String
from .NatNetClient import NatNetClient
import threading
from .DataDescriptions import DataDescriptions

latest_position = None  # global position variable
position_lock = threading.Lock()

class Publisher(Node):

    def __init__(self):
        super().__init__('location_publisher')
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.1 # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
       

    def timer_callback(self):
        global latest_position
        with position_lock:
            msg = String()
            msg.data = str(latest_position)
            self.publisher_.publish(msg)
            self.get_logger().info(msg.data)
            try:
                coords = tuple(map(float, msg.data.strip('()').split(',')))
                if len(coords) == 3:
                    x, y, z = coords
                    self.cf.extpos.send_extpos(x, y, z)
     
                else:
                    self.get_logger().error(f"Expected 3 coordinates but got {len(coords)}")
            except Exception as e:
                self.get_logger().error(f"Failed to parse coordinates: {e}")


    def rrbf(self,new_id, position, rotation):
        global latest_position
        with position_lock:
            latest_position = position
         

def start_natnet_client(publisher):
        
        local_ip="10.131.220.228"
        server_ip="10.131.206.160"

        #initialize client
        streaming_client = NatNetClient()
        streaming_client.set_use_multicast(False)
        streaming_client.set_client_address(local_ip)
        streaming_client.set_server_address(server_ip)
        print('client initialized')

        #assign rrbf function responsibility
        streaming_client.rigid_body_listener = publisher.rrbf

        #make it silent
        streaming_client.set_print_level(0)     

        #run instance
        streaming_client.run('d')

def main(args=None):
    
    rclpy.init(args=args)

    publisher = Publisher()

    # Start the NatNet client in a separate thread
    natnet_thread = threading.Thread(target=start_natnet_client, args=(publisher,))
    natnet_thread.start()

    try:
        # Spin the ROS2 node to process callbacks
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()