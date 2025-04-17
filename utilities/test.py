import cv2

# url = 'http://172.26.76.128:4747/video'
# cap = cv2.VideoCapture(url)
cap = cv2.VideoCapture(1)

if not cap.isOpened():
    print("Failed to open video stream.")
else:
    print("Connection successful.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame.")
        break
        
    cv2.imshow('Phone Camera', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
