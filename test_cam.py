import cv2
from ultralytics import YOLO

# 1. Load your custom trained model
print("Loading model 'best.pt'...")
try:
    model = YOLO('best.pt')
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    exit()

# 2. Open the default camera (index 0 is usually the built-in laptop camera)
print("Opening camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

print("Camera opened. Press 'q' to quit.")

# 3. Read frames and run inference
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    # Run YOLOv8 inference on the frame
    # verbose=False prevents printing a line for every single frame
    results = model(frame, verbose=False)

    # The results object contains the annotated frame
    # Plotting the results draws the bounding boxes and labels automatically
    annotated_frame = results[0].plot()

    # Display the annotated frame
    cv2.imshow("YOLOv8 Live Inference (Press 'q' to quit)", annotated_frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 4. Clean up
cap.release()
cv2.destroyAllWindows()
