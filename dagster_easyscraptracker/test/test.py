from ultralytics import YOLO

model = YOLO("./runs/classify/train/weights/best.pt")

results = model("./results/0/val/ball")

print(results)