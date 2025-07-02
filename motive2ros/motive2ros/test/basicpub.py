import sys
import time

import rclpy 
from rclpy.node import Node

from std_msgs.msg import String
from NatNetClient import NatNetClient




def rrbf(new_id, position, rotation):
        print(position)
        if len(position) == 3:
            x, y, z = position
            
     
        else:
            print('you suck at coding')

def start_natnet_client():
        
        local_ip="10.131.220.228"
        server_ip="10.131.196.172"

        #initialize client
        streaming_client = NatNetClient()
        streaming_client.set_use_multicast(False)
        streaming_client.set_client_address(local_ip)
        streaming_client.set_server_address(server_ip)
        print('client initialized')

        #assign rrbf function responsibility
        streaming_client.rigid_body_listener = rrbf

        #make it silent
        streaming_client.set_print_level(0)     

        #run instance
        streaming_client.run('d')
def main():
      
        start_natnet_client()
        
if __name__ == '__main__':

    main()