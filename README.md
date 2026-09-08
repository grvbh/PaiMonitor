# PaiMonitor Dashboard

Full-stack dashboard for the PaiMonitor AI/IoT insect trap: farmer login
(devices + field map + density charts) and admin login (all devices across
farmers), fed by a trained YOLOv8 model running on hourly trap images
uploaded by the device to S3.

## Architecture

```
PaiMonitor device --> S3 bucket --(event notification)--> SQS queue
                                                              |
                                                              v
                                                    ingest-worker (backend/app/services/s3_ingest.py)
                                                       - downloads image
                                                       - runs YOLOv8 inference
                                                       - writes Detection rows to Postgres
                                                              |
                                                              v
                                              FastAPI backend  <---- React dashboard (farmer / admin)
                                                              |
                                                       PostgreSQL
                                          (users, devices, trap_images, detections)
```

- **backend/** — FastAPI API: auth (JWT, farmer/admin roles), device
  management, image/detection listing, density analytics (day/week/month
  aggregation via SQL `date_trunc`), plus the S3→SQS ingestion worker.
- **frontend/** — React (Vite) dashboard: login, farmer view (device list,
  Leaflet map, density chart), admin view (all devices table + map).
- **ml-training/** — Everything to go from raw trap images (which is where
  you are now) to a deployed `.pt` model: sampling script, labeling
  workflow doc, YOLOv8 training script.

## Quick start (local dev)

```bash
cp backend/.env.example backend/.env
# fill in AWS creds, JWT secret, etc. in backend/.env

docker compose up --build
```
- API: http://localhost:8000/docs (FastAPI's auto-generated Swagger UI —
  useful for testing endpoints directly)
- Dashboard: http://localhost:5173

Create the first admin user:
```bash
docker compose exec backend python create_admin.py
```
Then log in as admin, register each farmer's device (assigns
serial number, lat/lon, and owner) via `POST /devices/` (from the Swagger
UI or a small admin form you can add later).

## Wiring up AWS (one-time, since the device already uploads to S3)

1. In the S3 bucket the device uploads to, add an **Event Notification**
   (Properties → Event notifications) for `s3:ObjectCreated:*` targeting
   a new SQS queue.
2. Put that queue's URL in `backend/.env` as `S3_EVENT_QUEUE_URL`.
3. Make sure device uploads follow a predictable key pattern so the
   ingestion worker can map an image back to a device:
   ```
   devices/{serial_number}/{yyyy-mm-dd}/{unix_timestamp}.jpg
   ```
   (`app/services/s3_ingest.py` parses this — adjust `KEY_PATTERN` there
   if your device firmware already uses a different scheme rather than
   changing the firmware.)
4. Give the backend IAM credentials `s3:GetObject` on the bucket and
   `sqs:ReceiveMessage`/`sqs:DeleteMessage` on the queue.

The `ingest-worker` container then picks up each new image within
seconds, runs it through the model, and stores per-species counts —
no manual button-press needed on the farmer's end.

## Model status

There's no trained model yet — `ml-training/README.md` walks through
labeling (Roboflow recommended) and training a YOLOv8s model tuned for
small-object detection on yellow sticky-trap images. Until a real model
is trained, drop any `.pt` file at
`backend/app/ml/weights/insect_detector.pt` (even an untrained/COCO
default) so the API doesn't crash on startup — detections just won't be
meaningful yet.

## Deploying beyond your own machine

- Simplest: any VM (EC2, Lightsail, DigitalOcean) with Docker — clone the
  repo, `docker compose up -d --build`, put a domain + TLS (Caddy or
  nginx + certbot) in front of the frontend container.
- Managed DB: swap the `db` service for RDS Postgres and point
  `DATABASE_URL` at it — better for backups/scaling than a container
  volume once farmers depend on this daily.
- The `ingest-worker` and `backend` can scale independently — if
  detection volume grows, run multiple `ingest-worker` replicas (SQS
  naturally load-balances across consumers).

## What's next
- Farmer/device self-signup flow (currently admin registers devices)
- SMS/WhatsApp alert wiring (brochure mentions this — not yet built;
  would hook into the ingestion worker once a density threshold is
  crossed)
- Spraying-time recommendation logic (brochure mentions this too — needs
  the temperature/humidity fields, already in the schema, wired from the
  device's sensor payload)
