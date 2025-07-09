from motive2ros.library import functions
import time
import threading
def main(id, uri, local = "10.131.220.228", server = "10.131.196.172"):
    uristring = 'radio://0/80/2M/' +  uri
    print(uristring)
    controller = functions.sc_flight(local, server, id, uristring)
    #controller.csv_logger(10)
    controller.takeoff(1, 5)
    if id == 10:
        controller.go_to(2,1,2,0,5)
        controller.go_to(2,-1,2,0,5)
        controller.go_to(-1,-1,2,0,5)
        controller.go_to(-1,1,2,0,5)
        controller.go_to(0,0,2,0,5)
    else:
        controller.go_to(2,1,1,0,5)
        controller.go_to(2,-1,1,0,5)
        controller.go_to(-1,-1,1,0,5)
        controller.go_to(-1,1,1,0,5)
        controller.go_to(1,0,1,0,5)
    controller.land(0,5)
    controller.disconnect()

if __name__=='__main__':
    main1 = threading.Thread(target=main, args=(10, 'E7E7E7E7E8',))
    main2 = threading.Thread(target=main, args=(11, 'E7E7E7E7E7',))
    
    main1.start()
    main2.start()

    main1.join()
    main2.join()