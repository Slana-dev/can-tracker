import math
from ultralytics import YOLO
import cv2

sirina = 480
visina = 360
verticalFov = 57
horizontalFov = 88
horizontalFov_rad = math.radians(horizontalFov)
verticalFov_rad = math.radians(verticalFov)


focalX = (sirina / 2) / math.tan(horizontalFov_rad / 2)
focalY = (visina / 2) / math.tan(verticalFov_rad / 2)


cap = cv2.VideoCapture(2)  
cap.set(cv2.CAP_PROP_FRAME_WIDTH, sirina)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, visina)
model=YOLO(r"best.pt") 
cap.set(cv2.CAP_PROP_FPS, 30)


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


# izracuna trenutno razdaljo
def trenutnaRazdalja(minInde, boxes): 
    x = boxes[minInde][0]
    y = boxes[minInde][1]
    dolzina = abs(x- int(sirina) // 2) + abs(y - int(visina) // 2)
    return dolzina

# najde indeks minimalne razdalje
def minDolzina(dolzine, n):
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
def kotKalkulator(boxes, minInde, smer):
    if smer == 'x':
        x = boxes[minInde][0]
        dolzina = abs(x- int(sirina) // 2)
        kotStopinje = math.degrees(math.atan(dolzina / focalX))
        return kotStopinje
    
    y = boxes[minInde][1]
    dolzina = abs(y- int(visina) // 2)
    kotStopinje = math.degrees(math.atan(dolzina / focalY))
    return kotStopinje

# Odmik po y glede na oddaljenost
def odmikOddaljenost(boxes, minInde):
    razmerje = visina / boxes[minInde][3]
    print(razmerje)

# Smer premika
def smerPremika(boxes, minInde, smer):
    if smer == 'x':
        x = boxes[minInde][0]
        dolzina = (x- int(sirina) // 2)
        if(dolzina > 0):
            return 'd'
        return 'a'
        
    
    y = boxes[minInde][1]
    dolzina = (y- int(visina) // 2)
    if(dolzina > 0):
        return 's'
    return 'w'


# izvede ukaze
def izvedi(minInde, n):
    counter = 0
    delay = 20
    while True:
        microsteping = '0'
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(
            source=frame,
            tracker="bytetrack.yaml",
            classes=[0],
            conf=0.1,
            iou=0.3,
            persist=True,
            #device='cuda',
            verbose= False
        )

        stBox = len(results[0].boxes)

        # Display
        anotacija= results[0].plot()
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
            razdalja = trenutnaRazdalja(minInde, boxes)
            print("Razdalja:", razdalja)
           
            if razdalja < 250:
                microsteping = '1'
                print("microstepping")

            smerX = smerPremika(boxes, minInde, 'x')
            smerY = smerPremika(boxes, minInde, 'y')
            kotX = kotKalkulator(boxes, minInde, 'x')
            kotY = kotKalkulator(boxes, minInde, 'y')
            odmikOddaljenost(boxes, minInde)
            print("smer" , smerX, smerY,"kot: ", kotX, kotY)

        counter+=1

        # Quit
        if cv2.waitKey(1) == ord('q'):
            break


def mainLoop():
    delay = 30
    frameCounter = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.track(
            source=frame,
            tracker="bytetrack.yaml",
            classes=[0],
            conf=0.1,
            iou=0.3,
            persist=True,
            #device='cuda',
            verbose= False
        )
        
        # Display
        anotacija= results[0].plot()
        cv2.circle(anotacija, (int(sirina) // 2, int(visina) // 2), 5, (0, 0, 255), -1)
        cv2.imshow("preview", anotacija)


        if frameCounter % delay == 0:
            n = len(results[0].boxes)
            if(n != 0):
                boxes = results[0].boxes.xywh.cpu().numpy()
                # Vse razdalje in minIndeks
                dolzine = kalkulatorRazdalj(boxes, n)
                minDolzinaInde = minDolzina(dolzine, n)
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




mainLoop()