from motive2ros.library import functions

controller = functions.sc_flight("10.131.220.228", "10.131.196.172", 5)
controller.takeoff()
controller.disconnect()
