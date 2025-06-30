import rclpy
from rclpy.node import Node
import time


from std_msgs.msg import String


import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.mem import MemoryElement
from cflib.crazyflie.mem import Poly4D
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper
from cflib.utils.reset_estimator import reset_estimator
from cflib.positioning.motion_commander import  MotionCommander

uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')

class MinimalSubscriber(Node):

    def __init__(self,cf):
        super().__init__('minimal_subscriber')
        self.cf = cf
        self.subscription = self.create_subscription(
            String,
            'topic',
            self.listener_callback,
            10)
        self.subscription  # prevent unused variable warning

    def listener_callback(self, msg):
        self.get_logger().info(msg.data)
        # self.cf.extpos.send_extpos(msg.data)
        try:
            coords = tuple(map(float, msg.data.strip('()').split(',')))
            if len(coords) == 3:
                x, y, z = coords
                self.cf.extpos.send_extpos(x, y, z)
     
            else:
                self.get_logger().error(f"Expected 3 coordinates but got {len(coords)}")
        except Exception as e:
            self.get_logger().error(f"Failed to parse coordinates: {e}")

    
        


def main(args=None):
    cflib.crtp.init_drivers()

    
    with SyncCrazyflie(uri, cf=Crazyflie(rw_cache='./cache')) as scf:
        cf = scf.cf
        rclpy.init(args=args)

        minimal_subscriber = MinimalSubscriber(cf)
        print('starting data feed')
        rclpy.spin(minimal_subscriber)
        print('starting flight plan')
        cf.platform.send_arming_request(True)
        time.sleep(1.0)
        commander = cf.high_level_commander
        commander.takeoff(1.0, 2.0)
        time.sleep(3.0)
        commander.land(0.0, 2.0)
        time.sleep(2)
        commander.stop()



    # Destroy the node explicitly
    # (optional - otherwise it will be done automatically
    # when the garbage collector destroys the node object)
    minimal_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()