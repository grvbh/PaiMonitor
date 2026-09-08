"""
Train the insect detector on a YOLO-format dataset exported from Roboflow/CVAT.

Usage:
  python train.py --data dataset/data.yaml --epochs 100 --imgsz 1024 --model yolov8s.pt
"""
import argparse

from ultralytics import YOLO


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="path to data.yaml")
    parser.add_argument("--model", default="yolov8s.pt", help="base weights to fine-tune from")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=1024)
    parser.add_argument("--batch", type=int, default=16)
    args = parser.parse_args()

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=20,           # early stop if val mAP stalls
        augment=True,
        mosaic=1.0,            # helpful for small, dense objects like insects
    )

    metrics = model.val()
    print("Validation metrics:", metrics.results_dict)
    print("\nBest weights saved under runs/detect/train*/weights/best.pt")
    print("Copy that file to backend/app/ml/weights/insect_detector.pt to deploy it.")


if __name__ == "__main__":
    main()
