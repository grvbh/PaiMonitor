"""
Device -> S3 -> (S3 Event Notification) -> SQS -> this worker -> DB.

Setup on the AWS side (one-time):
  1. S3 bucket (settings.s3_bucket) already receives uploads from the
     PaiMonitor devices, e.g. key pattern:
         devices/{serial_number}/{yyyy-mm-dd}/{unix_ts}.jpg
  2. Create an SQS queue, and add an S3 "Event Notification" on the bucket
     for `s3:ObjectCreated:*` that publishes to that queue.
  3. Put the queue URL in settings.s3_event_queue_url.

This worker long-polls the queue, so no polling/cron of the bucket itself
is needed and processing happens within seconds of each hourly upload.
Run it as a separate process/container: `python -m app.services.s3_ingest`
"""
import json
import re
import time
from datetime import datetime, timezone

import boto3
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app import models
from app.ml.infer import run_inference

KEY_PATTERN = re.compile(r"devices/(?P<serial>[^/]+)/.*?(?P<ts>\d{10,13})\.jpe?g$", re.IGNORECASE)

s3_client = boto3.client(
    "s3",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id or None,
    aws_secret_access_key=settings.aws_secret_access_key or None,
)
sqs_client = boto3.client(
    "sqs",
    region_name=settings.aws_region,
    aws_access_key_id=settings.aws_access_key_id or None,
    aws_secret_access_key=settings.aws_secret_access_key or None,
)


def _parse_key(key: str):
    m = KEY_PATTERN.search(key)
    if not m:
        return None, None
    ts_raw = m.group("ts")
    ts = int(ts_raw) / 1000 if len(ts_raw) == 13 else int(ts_raw)
    return m.group("serial"), datetime.fromtimestamp(ts, tz=timezone.utc)


def ingest_object(db: Session, bucket: str, key: str):
    serial, captured_at = _parse_key(key)
    if not serial:
        print(f"[ingest] skipping key with unrecognized pattern: {key}")
        return

    device = db.query(models.Device).filter(models.Device.serial_number == serial).first()
    if not device:
        print(f"[ingest] unknown device serial '{serial}', skipping key {key}")
        return

    image = models.TrapImage(
        device_id=device.id,
        s3_key=key,
        s3_bucket=bucket,
        captured_at=captured_at or datetime.now(timezone.utc),
    )
    db.add(image)
    device.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(image)

    try:
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        image_bytes = obj["Body"].read()
        detections = run_inference(image_bytes)

        for d in detections:
            x, y, w, h = d["bbox"]
            db.add(models.Detection(
                image_id=image.id,
                species=d["species"],
                confidence=d["confidence"],
                bbox_x=x, bbox_y=y, bbox_w=w, bbox_h=h,
            ))
        image.processed = True
        db.commit()
        print(f"[ingest] processed {key}: {len(detections)} detections")
    except Exception as e:
        image.processing_error = str(e)
        db.commit()
        print(f"[ingest] ERROR processing {key}: {e}")


def poll_forever():
    if not settings.s3_event_queue_url:
        raise RuntimeError("s3_event_queue_url is not configured")

    print("[ingest] polling SQS for new trap images...")
    while True:
        resp = sqs_client.receive_message(
            QueueUrl=settings.s3_event_queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
        )
        messages = resp.get("Messages", [])
        if not messages:
            continue

        db = SessionLocal()
        try:
            for msg in messages:
                body = json.loads(msg["Body"])
                for record in body.get("Records", []):
                    bucket = record["s3"]["bucket"]["name"]
                    key = record["s3"]["object"]["key"]
                    ingest_object(db, bucket, key)

                sqs_client.delete_message(
                    QueueUrl=settings.s3_event_queue_url,
                    ReceiptHandle=msg["ReceiptHandle"],
                )
        finally:
            db.close()


if __name__ == "__main__":
    poll_forever()
