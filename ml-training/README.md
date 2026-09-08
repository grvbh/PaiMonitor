# PaiMonitor Insect Detection — Training Pipeline

You currently have raw sticky-trap images, no labels. Here's the path from
that to a working model plugged into the dashboard.

## 1. Collect a labeling set
Pull ~500–1000 representative images from S3 covering different times of
day, seasons, trap fullness levels, and lighting. Use `pull_from_s3.py` to
grab a random sample instead of downloading everything.

```bash
python pull_from_s3.py --bucket paimonitor-trap-images --prefix devices/ --sample 800 --out ./raw_images
```

## 2. Define your species/class list
Decide the classes you actually need to distinguish for tomato IPM. A
reasonable starting set for tomato fields (adjust to your target region):
`whitefly`, `aphid`, `thrips`, `leafminer_fly`, `other`.

Fewer, well-separated classes will train much faster and more reliably
than a large fine-grained taxonomy — you can always split classes later
once you have more labeled data.

## 3. Annotate
Use **Roboflow** (free tier is enough to start, and it exports directly
in YOLO format) or **CVAT** if you want to self-host. Draw a bounding box
around each insect on the sticky trap and assign it a species label.

Because insects are small and numerous per image, budget real time here —
this is usually the actual bottleneck, not the training itself. Roboflow's
"smart polygon"/model-assisted labeling helps a lot once you have ~100
images labeled manually (it can pre-suggest boxes on the rest).

Export the annotated set as a **YOLOv8** dataset — you'll get a folder like:
```
dataset/
  images/train/*.jpg
  images/val/*.jpg
  labels/train/*.txt
  labels/val/*.txt
  data.yaml
```
Put that folder at `./dataset` in this directory (or point `train.py` at
wherever you exported it).

## 4. Train
```bash
pip install -r requirements.txt
python train.py --data dataset/data.yaml --epochs 100 --imgsz 1024 --model yolov8s.pt
```
- `imgsz 1024` (rather than the default 640) matters here: insects are
  small relative to the full trap image, and downscaling too aggressively
  loses them.
- Start from `yolov8s.pt` (small) — trap images are visually simple
  (yellow background, dark insects), so you don't need a huge backbone.
  Move to `yolov8m.pt` only if accuracy plateaus and you have >2000 images.
- Watch `runs/detect/train/results.png` for the loss/mAP curves.

## 5. Deploy the weights
Copy the resulting `runs/detect/train/weights/best.pt` to:
```
backend/app/ml/weights/insect_detector.pt
```
Restart the backend — `app/ml/infer.py` loads it lazily on first request.

## 6. Iterate
As the device uploads real field images and the model runs on them in
production, periodically pull a sample of *low-confidence* detections
(easy to query — filter `Detection.confidence < 0.5`) for re-labeling and
fold them back into the training set. This active-learning loop is the
fastest way to improve accuracy over time without re-labeling everything.
