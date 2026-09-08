"""
Pull a random sample of raw trap images from S3 to build a labeling set.

Usage:
  python pull_from_s3.py --bucket paimonitor-trap-images --prefix devices/ \
      --sample 800 --out ./raw_images
"""
import argparse
import os
import random

import boto3


def list_all_keys(s3, bucket, prefix):
    keys = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].lower().endswith((".jpg", ".jpeg", ".png")):
                keys.append(obj["Key"])
    return keys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--prefix", default="")
    parser.add_argument("--sample", type=int, default=500)
    parser.add_argument("--out", default="./raw_images")
    parser.add_argument("--region", default="ap-south-1")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)
    s3 = boto3.client("s3", region_name=args.region)

    print(f"Listing objects under s3://{args.bucket}/{args.prefix} ...")
    keys = list_all_keys(s3, args.bucket, args.prefix)
    print(f"Found {len(keys)} images.")

    sample = random.sample(keys, min(args.sample, len(keys)))
    for i, key in enumerate(sample, 1):
        local_name = key.replace("/", "__")
        s3.download_file(args.bucket, key, os.path.join(args.out, local_name))
        if i % 50 == 0:
            print(f"  downloaded {i}/{len(sample)}")

    print(f"Done. {len(sample)} images saved to {args.out}")


if __name__ == "__main__":
    main()
