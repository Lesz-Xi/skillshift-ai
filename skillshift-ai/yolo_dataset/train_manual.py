from ultralytics import YOLO

# Load a pre-trained model
model = YOLO('yolov8n.pt')

# Train the model
results = model.train(data='/Users/lesz/Documents/Project-AI/skillshift-ai/yolo_dataset/configs/dataset.yaml', epochs=100, imgsz=640)

# Export the model to ONNX format
model.export(format='onnx')
