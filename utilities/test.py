import cv2

# Replace with your phone's IP address and port shown in the IP webcam app
url = 'http://172.26.65.246:4747/video'
cap = cv2.VideoCapture(url)

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    # Display the frame (we'll add detection code here later)
    cv2.imshow('Phone Camera', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()