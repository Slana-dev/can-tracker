from ultralytics import YOLO
import cv2

sirina = 1280
visina = 720

cap = cv2.VideoCapture(2)  
cap.set(cv2.CAP_PROP_FRAME_WIDTH, sirina)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, visina)
model=YOLO(r"best.pt")
cap.set(cv2.CAP_PROP_FPS, 60)



#vrne vse razdalje
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

#izracuna trenutno razdaljo
def trenutnaRazdalja(minInde, boxes):
    x = boxes[minInde][0]
    y = boxes[minInde][1]
    dolzina = abs(x- int(sirina) // 2) + abs(y - int(visina) // 2)
    return dolzina

#najde indeks minimalne razdalje
def minDolzina(dolzine, n):
    min = 100000
    i = 0
    minInde = -1
    for i in range(n):
        if dolzine[i] < min:
            min = dolzine[i]
            minInde = i
        i+=1
    return minInde

#izvede ukaze
def izvedi(minInde, n):
    counter = 0
    delay = 20
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
            device='cuda',
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
            print("Razdalja:",razdalja)
            # Ce razdalja manjsa vklopi microstepping
            if razdalja < 200:
                print("microstepping")
            print("sending info")

        counter+=1

        # Quit
        if cv2.waitKey(1) == ord('q'):
            break


#MAIN
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
