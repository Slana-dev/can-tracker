import math
import struct
from ultralytics import YOLO
import cv2
import serial
import time
import keyboard

# VARIABLES
sirina = 1280
visina = 720
verticalFov = 57
horizontalFov = 88
horizontalFov_rad = math.radians(horizontalFov)
verticalFov_rad = math.radians(verticalFov)
focalX = (sirina / 2) / math.tan(horizontalFov_rad / 2)
focalY = (visina / 2) / math.tan(verticalFov_rad / 2)



# DISPLAY
cap = cv2.VideoCapture(1,cv2.CAP_DSHOW)  
cap.set(cv2.CAP_PROP_FRAME_WIDTH, sirina)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, visina)
model=YOLO(r"best.pt") 
cap.set(cv2.CAP_PROP_FPS, 60)

# Show display
performance = True

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
    min = 1000000
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
        return kotStopinje - kotStopinje//3
    
    y = boxes[minInde][1]
    dolzina = abs(y - odmikY- int(visina) // 2)
    kotStopinje = math.degrees(math.atan(dolzina / focalY))
    return kotStopinje - kotStopinje//3


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


# izvede ukaze
def izvedi(minInde, n):
    counter = 0
    delay = 2
    tolerancaStopinj = 1.3
    while True:
        microX = 0
        microY = 0
        ret, frame = cap.read()

        if not ret:
            break

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

        stBox = len(results[0].boxes)

        # Display
        anotacija= results[0].plot()
        if(performance):
            cv2.circle(anotacija, (int(sirina) // 2, int(visina) // 2), 5, (0, 0, 255), -1)
            cv2.imshow("preview", anotacija)

        # In case a box is lost
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
            if razdaljaX < 300:
                microX = 1
            if razdaljaY < 300:
                microY = 1
            
            odmikY = odmikOddaljenost(boxes, minInde)

            smerX = smerPremika(boxes, minInde, 'x', 0)
            smerY = smerPremika(boxes, minInde, 'y', odmikY)
            
            kotX = kotKalkulator(boxes, minInde, 'x', 0)
            kotY = kotKalkulator(boxes, minInde, 'y', odmikY)
            stepX = (round)(kotX // (1.8))
            stepY = (round)(kotY // (1.8))

            if(kotX < tolerancaStopinj):
                stepX = 0
            if(kotY < tolerancaStopinj):
                stepY = 0

            sendCommand(smerX, smerY, stepX, stepY, microX, microY)
            print("smer" , smerX, smerY,"kot: ", kotX, kotY, "steps: ", stepX, stepY)

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
        if(performance):
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
                print("FREE ROAM")

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

        if(performance):
            cv2.circle(frame, (int(sirina) // 2, int(visina) // 2), 5, (0, 0, 255), -1)
            cv2.imshow("preview", frame)

        if keyboard.is_pressed('w'):
            sendCommand(-1, -1, 0, 3, 1, 1)
        elif keyboard.is_pressed('s'):
            sendCommand(1, 1, 0, 3, 1, 1)
        elif keyboard.is_pressed('d'):
            sendCommand(1, 1, 3, 0, 1, 1)
        elif keyboard.is_pressed('a'):
            sendCommand(-1, -1, 3, 0, 1, 1)

        # Quit with 
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
    print("-----------------")
    mainLoop()
