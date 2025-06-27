from ultralytics import YOLO
import cv2

cap = cv2.VideoCapture(2)  
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
model=YOLO(r"C:\Users\ambro\OneDrive\Desktop\yolov8\best.pt")
cap.set(cv2.CAP_PROP_FPS, 60)


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


frameCounter = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

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
    
    #display
    anotacija= results[0].plot()
    cv2.imshow("preview", anotacija)


    if frameCounter % 10 == 0:
        n = len(results[0].boxes)
        if(n != 0):
            print("detected:", n)
            boxes = results[0].boxes.xywh.cpu().numpy()
            dolzine = kalkulatorRazdalj(boxes, n, 1280/2, 720/2)
            minDolzinaInde = minDolzina(dolzine, n)
            if(minDolzinaInde != -1):
                print(minDolzinaInde, dolzine[minDolzinaInde])
        
        
    #quit
    if cv2.waitKey(1) == ord('q'):
        break
    frameCounter+=1

cap.release()
cv2.destroyAllWindows()
