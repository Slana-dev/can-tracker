import math
import struct
from ultralytics import YOLO
import cv2
import serial
import time
import keyboard

# SCREEN VARIABLES
sirina = 1280
visina = 720
verticalFov = 57
horizontalFov = 58
horizontalFov_rad = math.radians(horizontalFov)
verticalFov_rad = math.radians(verticalFov)
focalX = (sirina / 2) / math.tan(horizontalFov_rad / 2)
focalY = (visina / 2) / math.tan(verticalFov_rad / 2)
windowName = "preview"

# POSITION VARIABLES
posX = 0
posY = 0
mejaKot = 54

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
arduino = serial.Serial(port='COM4', baudrate=9600, timeout=1)
time.sleep(2)

# Manual settings
manual = False

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


# Odmik po y glede na oddaljenost za natancnost
def odmikOddaljenost(boxes, minInde):
    heightBox = boxes[minInde][3]
    razmerje = heightBox / visina
    
    if razmerje > 0.3:
        return 0
    elif razmerje <= 0.3 and razmerje > 0.2:
        return heightBox / 4
    elif razmerje <= 0.2 and razmerje > 0.1:
        return heightBox/ 2
    else: 
        return heightBox


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
        return 1
    return -1

# Poslje komando
def sendCommand(smerX, smerY, stepX, stepY, microX, microY):
    buffer= struct.pack(
        '<bbBBBB',
        smerX, 
        smerY, 
        stepX, 
        stepY, 
        microX,
        microY
    )
    arduino.write(buffer)
    return

# Recenter at the start
def onEdgeX():
    readX = arduino.read(1)  
    if readX == b'1':
        return True
    return False

def onEdgeY():
    readY = arduino.read(1)  
    if readY == b'2':
        return True
    return False

def recenterX():
    edgeX = onEdgeX()
    while not edgeX:
        sendCommand(1,0,3,0,0,0)
        edgeX = onEdgeX()
    sendCommand(-1,0,60,0,1,1)      

def recenterY(): 
    edgeY = onEdgeX()
    while not edgeY:
        sendCommand(0,1,0,3,0,0)
        edgeY = onEdgeY()
    sendCommand(0,-1,0,60,1,1)  

# izvede ukaze
def izvedi(minInde, n):
    counter = 0
    delay = 1
    global posY, posX
    while True:
        microX = 0
        microY = 0

        ret, frame = cap.read()
        if not ret:
            break

        if keyboard.is_pressed('r'):
            recenterX()
            time.sleep(2)
            recenterY()
            time.sleep(2)
            posX = 0
            posY = 0
        
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
            cv2.imshow(windowName, anotacija)

        # In case a box is lost
        stBox = len(results[0].boxes)
        if stBox != n:
            print("RESET\n") 
            return
        
        boxes = results[0].boxes.xywh.cpu().numpy()

        # In case indexes shift
        if minInde >= len(boxes):
            print("RESET\n")  
            return
        
        # Move the robot
        if counter % delay == 0:
            
            razdaljaX = razdaljaVzdolzOsi('x', minInde, boxes)
            razdaljaY = razdaljaVzdolzOsi('y', minInde, boxes)
            print(razdaljaX, razdaljaY)

            if razdaljaX < 250:
                microX = 1
            if razdaljaY < 250:
                microY = 1
            
            odmikY = odmikOddaljenost(boxes, minInde)

            smerX = smerPremika(boxes, minInde, 'x', 0)
            smerY = smerPremika(boxes, minInde, 'y', odmikY)
            
            kotX = kotKalkulator(boxes, minInde, 'x', 0)
            kotY = kotKalkulator(boxes, minInde, 'y', odmikY)
            stepX = (round)(kotX // (1.8))
            stepY = (round)(kotY // (1.8))
            if kotX > 1:
                posX += kotX * smerX
            if kotY > 1: 
                posY += kotY * smerY
            
            if posX < mejaKot and posY < mejaKot:
                sendCommand(smerX, smerY, stepX, stepY, microX, microY)
            else: 
                print("object out of bounds -> PLEASE RECENTER")
                print(posX, posY)
            #print("smer" , smerX, smerY,"kot: ", kotX, kotY, "steps: ", stepX, stepY)

        counter+=1

        # Quit
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return   


def mainLoop():
    delay = 20
    frameCounter = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Reset position
        if keyboard.is_pressed('r'):
            recenterX()
            time.sleep(2)
            recenterY()
            posX = 0
            posY = 0
            
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

        if frameCounter % delay == 0:
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
                
        frameCounter+=1
        
        # Quit
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    
    return

def Manual():
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if(display):
            cv2.circle(frame, (int(sirina) // 2, int(visina) // 2), 5, (0, 0, 255), -1)
            cv2.imshow("preview", frame)

        if keyboard.is_pressed('w'):
            sendCommand(-1, -1, 0, 3, 0, 0)
        elif keyboard.is_pressed('s'):
            sendCommand(1, 1, 0, 3, 0, 0)
        elif keyboard.is_pressed('d'):
            print(2)
            sendCommand(1, 1, 2, 0, 0, 0)
        elif keyboard.is_pressed('a'):
            sendCommand(-1, -1, 3, 0, 0, 0)

     # Quit
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
    print("SPACE / shoot")
    print("Q / quit")
    print("-----------------")
    Manual()
else:
    print("AUTOMATIC")
    print("-----------------")
    print("controls:")
    print("Q / quit")
    print("R / recenter position")
    print("-----------------")
    mainLoop()
