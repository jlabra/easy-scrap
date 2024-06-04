from ultralytics import YOLO

def main():
  model = YOLO("yolov8x-cls.pt")  # load a pretrained model (recommended for training)
  results = model.train(data="./results/0", epochs=10, imgsz=64)

if __name__ == "__main__":
  main()