from motive2ros.library.nodeflight import MocapCaller
import time
import rclpy
def main(): 
    ids = {10,11}
    MocapCaller("10.131.220.228","10.131.196.172", ids)


if __name__ == '__main__':
    main()
    
