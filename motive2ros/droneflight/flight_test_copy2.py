import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from library.NatNetClient import NatNetClient
import threading
import time

import cflib.crtp
from cflib.crazyflie import Crazyflie
from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
from cflib.utils import uri_helper

class MocapCrazyflieNode(Node):
    def __init__(self):
        super().__init__('mocap_crazyflie_node')

        self.publisher = self.create_publisher(PoseStamped, 'drone_pose', 10)
        self.subscription = self.create_subscription(PoseStamped, 'drone_pose', self.pose_callback, 10)

        self.lock = threading.Lock()
        self.latest_pose = None

        # Crazyflie setup
        self.uri = uri_helper.uri_from_env(default='radio://0/80/2M/E7E7E7E7E7')
        cflib.crtp.init_drivers()
        self.cf = Crazyflie(rw_cache='./cache')
        self.scf = SyncCrazyflie(self.uri, cf=self.cf)

        try:
            self.scf.open_link()
            self.get_logger().info("Connected to Crazyflie")
            self.cf.param.set_value('stabilizer.estimator', '2')
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Crazyflie: {e}")
            self.scf = None

        # NatNet Client setup
        self.client = NatNetClient()
        self.client.set_use_multicast(False)
        self.client.set_client_address("10.131.220.228")  # YOUR local IP
        self.client.set_server_address("10.131.206.160")  # YOUR Motive server IP
        self.client.rigid_body_listener = self.receive_rigid_body_frame
        self.client.set_print_level(0)

        # Start NatNet in thread
        self.natnet_thread = threading.Thread(target=self.run_natnet_client, daemon=True)
        self.natnet_thread.start()

        # ROS2 timer to publish pose 10Hz
        self.create_timer(0.1, self.publish_pose)

    def run_natnet_client(self):
        self.get_logger().info("Starting NatNet client run loop...")
        try:
            # Note: The original code used 'd' as argument to run(), which is undocumented
            # Use run() without arguments, or pass 'd' if your NatNetClient requires it
            if hasattr(self.client.run, '__call__'):
                success = self.client.run('d')  # Try 'd' argument if your SDK needs it
            else:
                success = self.client.run()
            if success:
                self.get_logger().info("NatNet client running")
            else:
                self.get_logger().error("NatNet client failed to start")
        except Exception as e:
            self.get_logger().error(f"Exception in NatNet client thread: {e}")

        # Keep thread alive while ROS node is alive
        while rclpy.ok():
            time.sleep(0.1)

    def receive_rigid_body_frame(self, new_id, position, rotation):
        pose = PoseStamped()
        pose.header.stamp = self.get_clock().now().to_msg()
        pose.header.frame_id = "map"

        pose.pose.position.x = position[0]
        pose.pose.position.y = position[1]
        pose.pose.position.z = position[2]

        pose.pose.orientation.x = rotation[0]
        pose.pose.orientation.y = rotation[1]
        pose.pose.orientation.z = rotation[2]
        pose.pose.orientation.w = rotation[3]

        with self.lock:
            self.latest_pose = pose

    def publish_pose(self):
        with self.lock:
            if self.latest_pose:
                self.publisher.publish(self.latest_pose)

    def pose_callback(self, msg: PoseStamped):
        if not self.scf or not self.scf.cf:
            return

        p = msg.pose.position
        o = msg.pose.orientation

        self.cf.extpos.send_extpose(p.x, p.z, p.y, o.x, o.y, o.z, o.w)
        self.get_logger().info(f"Sent pose to Crazyflie: x={p.x:.2f} y={p.y:.2f} z={p.z:.2f}")

def main(args=None):
    rclpy.init(args=args)
    node = MocapCrazyflieNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down node")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()