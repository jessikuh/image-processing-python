from io import BytesIO
from PIL import Image, ImageOps
import boto3
import json
import os
import requests
import tempfile
from subprocess import call

ENVIRONMENT = os.environ.get("ENV", "development")

if ENVIRONMENT == "development":
    from dotenv import load_dotenv

    load_dotenv()

BUCKET = os.environ.get("AWS_BUCKET")
ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID")
SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
REGION = os.environ.get("AWS_REGION")
CLOUDFLARE_ZONE_ID = os.environ.get("CLOUDFLARE_ZONE_ID")
CLOUDFLARE_EMAIL = os.environ.get("CLOUDFLARE_EMAIL")
CLOUDFLARE_KEY = os.environ.get("CLOUDFLARE_KEY")


def resize_gif(image, dimensions):
    frames = []
    duration_info = []
    size = image.size

    for frame_num in range(0, image.n_frames):
        image.seek(frame_num)
        new_frame = Image.new("RGBA", size)
        new_frame.paste(image, (0, 0), image.convert("RGBA"))
        new_frame = resize_image(new_frame, dimensions)
        frames.append(new_frame)
        duration_info.append(image.info["duration"])

    return frames, duration_info


def resize_image(image, dimensions):
    height, width = dimensions

    return ImageOps.fit(image, (width, height), Image.ANTIALIAS)


def save_image(image, **kwargs):
    imgByteArr = BytesIO()

    image.save(imgByteArr, **kwargs)

    return imgByteArr.getvalue()


def upload_image(key, filesToDelete, contentType, imgByteArr):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=ACCESS_KEY,
        aws_secret_access_key=SECRET_KEY,
        region_name=REGION,
    )

    s3.delete_objects(Bucket=BUCKET, Delete={"Objects": filesToDelete, "Quiet": True})

    if "gif" in contentType:
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(imgByteArr)
        f.close()
        filename = f.name
        call(["./scripts/s3_upload.sh", filename, key, contentType])
        os.unlink(f.name)
    else:
        s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=imgByteArr,
            ContentType=contentType,
            CacheControl="public, max-age=604800, immutable",
        )

    url = "https://assets.solusorbis.com/{}".format(key)
    data = {"files": [url]}

    cloudFlareRequest = requests.post(
        url="https://api.cloudflare.com/client/v4/zones/{}/purge_cache".format(
            CLOUDFLARE_ZONE_ID
        ),
        data=json.dumps(data),
        headers={
            "X-Auth-Email": CLOUDFLARE_EMAIL,
            "X-Auth-Key": CLOUDFLARE_KEY,
            "Content-Type": "application/json",
        },
    )

    if cloudFlareRequest.status_code == 200:
        return {
            "success": True,
            "url": url,
        }
    else:
        return {"success": False, "message": "There was an error uploading your file."}
