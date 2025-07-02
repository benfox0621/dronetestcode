from motive2ros.library.functions import mocap_basic_sub
import rclpy
from rclpy.node import Node

def main():
    rclpy.init()

    subscriber = mocap_basic_sub(6)
    try: 
        rclpy.spin(subscriber)
    except KeyboardInterrupt:
        pass
    finally:
        subscriber.destroy_node()

        rclpy.shutdown()

if __name__ == '__main__':
    main()