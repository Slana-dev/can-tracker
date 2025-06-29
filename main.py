from ultralytics import YOLO
import cv2

sirina = 1280
visina = 720

cap = cv2.VideoCapture(2)  
cap.set(cv2.CAP_PROP_FRAME_WIDTH, sirina)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, visina)
model=YOLO(r"best.pt")
cap.set(cv2.CAP_PROP_FPS, 30)

#vrne rezultate 
def retResults(frame):
     results = model.track(
        source=frame,
        tracker="bytetrack.yaml",
        classes=[0],
        conf=0.2,
        iou=0.3,
        persist=True,
       #device='cuda',
        verbose= False
    )
    return results

#vrne vse razdalje
def kalkulatorRazdalj(boxes, len, centerX, centerY):
    i = 0
    razdalje = []
    for i in range(len):
        x = boxes[i][0]
        y = boxes[i][1]
        dolzina = abs(x- centerX) + abs(y - centerY)
        razdalje.append(dolzina)
        i+=1
    return razdalje

#izracuna trenutno razdaljo
def trenutnaRazdalja(minInde, centerX, centerY, boxes):
    x = boxes[minInde][0]
    y = boxes[minInde][1]
    dolzina = abs(x- centerX) + abs(y - centerY)
    return dolzina

#najde indeks minimalne razdalje
def minDolzina(dolzine, n):
    min = 10000
    i= 0
    minInde = -1
    for i in range(n):
        if dolzine[i] < min:
            min = dolzine[i]
            minInde = i
        i+=1
    return minInde

#izvede ukaze
def ukazi(minInde, boxes, centerY, centerX, n):
    counter = 0
    delay = 5
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = retResults(frame)
        stBox = len(results[0].boxes)

        # Display
        anotacija= results[0].plot()
        cv2.imshow("preview", anotacija)
        cv2.circle(frame, (sirina/2, visina/2), 5, (0, 0, 255), -1)

        # In case a box is lost
        if stBox < n:
            return

        boxes = results[0].boxes.xywh.cpu().numpy()

        # In case indexes shift
        if minInde >= len(boxes):  
            return

        razdalja = trenutnaRazdalja(minInde, centerX, centerY, boxes)
        print("Razdalja:",razdalja)

        # Ce razdalja manjsa vklopi microstepping
        if counter % delay == 0:
            if razdalja < 40:
                print("microstepping")
            print("sending info")

    counter+=1

        # Quit
        if cv2.waitKey(1) == ord('q'):
            break


#MAIN
delay = 10
frameCounter = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = retResults(frame)
    
    # Display
    anotacija= results[0].plot()
    cv2.imshow("preview", anotacija)
    cv2.circle(frame, (sirina/2, visina/2), 5, (0, 0, 255), -1)

    if frameCounter % delay == 0:
        n = len(results[0].boxes)
        if(n != 0):
            print("detected:", n)
            boxes = results[0].boxes.xywh.cpu().numpy()
            # Vse razdalje in minIndeks
            dolzine = kalkulatorRazdalj(boxes, n, sirina/2, visina/2)
            minDolzinaInde = minDolzina(dolzine, n)
            # Izvedi ukaze za minIndeks
            print("Najblizji:",minDolzinaInde, dolzine[minDolzinaInde])
            ukazi(minDolzinaInde,boxes, sirina/2, visina/2, n)

    frameCounter+=1
      
    # Quit
    if cv2.waitKey(1) == ord('q'):
        break
    

cap.release()
cv2.destroyAllWindows()
