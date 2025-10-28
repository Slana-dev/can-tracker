import math
import struct
from ultralytics import YOLO
import cv2
import serial
import time
import keyboard

# SCREEN VARIABLES
sirinaOffset = 10
sirina = 1280 + sirinaOffset
visina = 720
verticalFov = 60
horizontalFov = 60
horizontalFov_rad = math.radians(horizontalFov)
verticalFov_rad = math.radians(verticalFov)
focalX = (sirina / 2) / math.tan(horizontalFov_rad / 2)
focalY = (visina / 2) / math.tan(verticalFov_rad / 2)
windowName = "preview"

# DISPLAY
cap = cv2.VideoCapture(1,cv2.CAP_DSHOW)  
cap.set(cv2.CAP_PROP_FRAME_WIDTH, sirina)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, visina)
model=YOLO(r"best.pt") 
cap.set(cv2.CAP_PROP_FPS, 60)
cv2.namedWindow(windowName)
cv2.moveWindow(windowName, 0, 0)

# SHOW DISPLAY
display = True

# ARDUINO
arduino = serial.Serial(port='COM5', baudrate=9600, timeout=1)
time.sleep(2)

# Manual control
manual = False

# speed
standby = 2
shoot = 3

# vrne vse razdalje
def kalkulatorRazdalj(boxes, len):
    i = 0
    razdalje = []
    for i in range(len):
        x = boxes[i][0]
        y = boxes[i][1]
        dolzina = abs(x- int(sirina) // 2) + abs(y - int(visina) // 2)
        razdalje.append(dolzina)
        i+=1
    return razdalje


# najde indeks minimalne razdalje
def minRazdaljaIndeks(dolzine, n):
    min = 10000
    i = 0
    minInde = -1
    for i in range(n):
        if dolzine[i] < min:
            min = dolzine[i]
            minInde = i
        i+=1
    return minInde


# Izracuna kot
def kotKalkulator(boxes, minInde, smer, odmikY):
    if smer == 'x':
        x = boxes[minInde][0]
        dolzina = abs(x- int(sirina) // 2) 
        kotStopinje = math.degrees(math.atan(dolzina / focalX))
        return kotStopinje  
    
    y = boxes[minInde][1]
    dolzina = abs(y - odmikY- int(visina) // 2)
    kotStopinje = math.degrees(math.atan(dolzina / focalY))
    return kotStopinje 


# vrne razdaljo vzdolz podate osi
def razdaljaVzdolzOsi(os, minInde, boxes):
    if os == 'x':
        return abs(sirina//2 - boxes[minInde][0])
    elif os == 'y':
        return abs(visina//2 - boxes[minInde][1])


# Smer premika
def smerPremika(boxes, minInde, smer, odmikY):
    if smer == 'x':
        x = boxes[minInde][0]
        dolzina = (x- int(sirina) // 2)
        if(dolzina > 0):
            return 1
        return -1
    
    y = boxes[minInde][1]
    dolzina = (y - odmikY- int(visina) // 2)
    if(dolzina > 0):
        return -1
    return 1

# Poslje komando
def sendCommand(smerX, smerY, stepX, stepY, speed1, speed2, polz, multX, multY):
    buffer= struct.pack(
        '<bbBBBBBBB',
        smerX, 
        smerY, 
        stepX, 
        stepY, 
        speed1,
        speed2,
        polz,
        multX,
        multY
    )
    arduino.write(buffer)
    return

# Recenter 
def recenter():
    data = arduino.read(arduino.in_waiting)
    if data == '1':
        sendCommand(0,-1,0,60,standby,standby,0,8,8)
    else:
        sendCommand(-1,0,60,0,standby,standby,0,8,8)

    arduino.reset_input_buffer()
    return

# pospesevanje motorjev za streljanje
def standbyThrottle():
    sendCommand(0,0,0,0,0,0,0,1,1)
    print("prizgi esc")
    time.sleep(15)
    sendCommand(0,0,0,0,1,1,0,1,1)
    time.sleep(0.6)
    sendCommand(0,0,0,0,0,0,0,1,1)
    time.sleep(0.1)
    sendCommand(0,0,0,0,1,1,0,1,1)
    time.sleep(1)
    sendCommand(0,0,0,0,standby,standby,0,1,1)
    print("konec")

def streljaj():
    sendCommand(0,0,0,0,shoot,shoot,1,1,1)

# izvede ukaze
def izvedi(minInde, n):
    standbyCopy = standby

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if(keyboard.is_pressed('space')):
            sendCommand(0,0,0,0,0,0,0,1,1)
        
        if(keyboard.is_pressed('e')):
            arduino.reset_input_buffer()
        
        if arduino.in_waiting > 0:
            recenter()

        results = model.track(
            source=frame,
            tracker="bytetrack.yaml",
            classes=[0],
            conf=0.2,
            iou=0.3,
            persist=True,
            device='cuda',
            verbose= False
        )

        # Display
        anotacija= results[0].plot()
        if(display):
            cv2.circle(anotacija, (int(sirina) // 2, int(visina) // 2), 5, (0, 0, 255), -1)
            cv2.imshow(windowName, anotacija)

        # In case a box is lost
        stBox = len(results[0].boxes)
        if stBox != n:
            print("RESET\n") 
            # return turret to standby
            sendCommand(0,0,0,0,standbyCopy, standbyCopy,0,1,1)
            return
        
        boxes = results[0].boxes.xywh.cpu().numpy()

        # In case indexes shift
        if minInde >= len(boxes):
            # return turret to standby
            sendCommand(0,0,0,0,standbyCopy, standbyCopy,0,1,1)
            print("RESET\n")  
            return
        
        # Move the robot
        multiplyX = 16
        multiplyY = 16
        smerX = smerPremika(boxes, minInde, 'x', 0)
        smerY = smerPremika(boxes, minInde, 'y', 0)
        
        kotX = kotKalkulator(boxes, minInde, 'x', 0)
        kotY = kotKalkulator(boxes, minInde, 'y', 0)

        stepX = (round)(kotX / (1.8))
        stepY = (round)(kotY / (1.8))

        if kotX < 1.8:
            stepX = round(kotX * 16 / 1.8)
            multiplyX = 1
        if kotY < 1.8:
            stepY = round(kotY * 16 / 1.8)

        if kotX < 0.5 and kotY < 1.8:
            stepX = 0 
            stepY = 0

        if stepX > 0 or stepY > 0:
                sendCommand(smerX, smerY, stepX, stepY, standbyCopy, standbyCopy,0,multiplyX, multiplyY )
        else:
            print("shooting!")
            streljaj()

        # Quit
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return   

def mainLoop():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if(keyboard.is_pressed('space')):
            sendCommand(0,0,0,0,0,0,0,1,1)

        if arduino.in_waiting > 0:
            recenter()

        results = model.track(
            source=frame,
            tracker="bytetrack.yaml",
            classes=[0],
            conf=0.15,
            iou=0.3,
            persist=True,
            device='cuda',
            verbose= False
        )
        
        # Display
        anotacija= results[0].plot()
        if(display):
            cv2.circle(anotacija, (int(sirina) // 2, int(visina) // 2), 5, (0, 0, 255), -1)
            cv2.imshow("preview", anotacija)

        
        n = len(results[0].boxes)
        if(n != 0):
            boxes = results[0].boxes.xywh.cpu().numpy()
            # Vse razdalje in minIndeks
            dolzine = kalkulatorRazdalj(boxes, n)
            minDolzinaInde = minRazdaljaIndeks(dolzine, n)
            # Izvedi ukaze za minIndeks
            print("Najblizji:",minDolzinaInde, dolzine[minDolzinaInde])
            izvedi(minDolzinaInde, n)
        else:
            print("NO CANS")
        
        # Quit
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    
    return

def Manual():
    standbyCopy = standby
    shootCopy = shoot
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if(display):
            cv2.circle(frame, (int(sirina) // 2, int(visina) // 2), 5, (0, 0, 255), -1)
            cv2.imshow("preview", frame)

        if keyboard.is_pressed('w'):
            sendCommand(1, 1, 0, 10,standbyCopy, standbyCopy,0,1,1)
        elif keyboard.is_pressed('s'):
            sendCommand(-1, -1, 0, 10, standbyCopy, standbyCopy,0,1,1)
        elif keyboard.is_pressed('d'):
            sendCommand(1, 1, 10, 0,standbyCopy, standbyCopy,0,1,1)
        elif keyboard.is_pressed('a'):
            sendCommand(-1, -1, 10, 0,standbyCopy, standbyCopy,0,1,1)
        elif keyboard.is_pressed('enter'):
            sendCommand(0,0,0,0,shootCopy, shootCopy,1,1,1)
        else:
            sendCommand(0,0,0,0, standbyCopy, standbyCopy,0,1,1)   
     
        if keyboard.is_pressed('space'):
            sendCommand(0,0,0,0, 0,0,0,1,1) 

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return       

if manual:
    print("MANUAL")
    print("-----------------")
    print("controls:")
    print("W / up")
    print("S / down")
    print("D / right")
    print("A / left")
    print("ENTER / shoot")
    print("Q / quit")
    print("-----------------")
    arduino.reset_input_buffer()
    standbyThrottle()
    Manual()
else:
    print("AUTOMATIC")
    print("-----------------")
    print("controls:")
    print("Q / quit")
    print("R / recenter position")
    print("-----------------")
    arduino.reset_input_buffer()
    standbyThrottle()
    mainLoop()
