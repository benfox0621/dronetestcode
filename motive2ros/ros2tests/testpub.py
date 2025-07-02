from motive2ros.library.functions import mocap_basic_pub
import rclpy
from rclpy.node import Node

def main():
    rclpy.init()

    publisher = mocap_basic_pub()
    try: 
        rclpy.spin(publisher)
    except KeyboardInterrupt:
        pass
    finally:
        publisher.destroy_node()

        rclpy.shutdown()

if __name__ == '__main__':
    main()
