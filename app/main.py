from core.functions import resize_image, resize_gif, save_image, upload_image
from fastapi import FastAPI, File, Form, Request, status
from fastapi.responses import JSONResponse
from io import BytesIO
from PIL import Image
import os
import time

# Environment variables
ENVIRONMENT = os.environ.get("ENV", "development")
BEARER_TOKEN = os.environ.get("ACCESS_TOKEN", "1a2b3c4d5e6f")

app = FastAPI()


@app.middleware("http")
async def check_bearer_token(request: Request, call_next):
    authorization = request.headers.get("Authorization", None)
    bearer = authorization.split()[1]

    if bearer != BEARER_TOKEN:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content="You are not authorized to access this resource.",
        )

    response = await call_next(request)
    return response


@app.post("/")
async def index(
    image: bytes = File(...),
    height: int = Form(...),
    width: int = Form(...),
    user_id: str = Form(...),
):
    keyPath = "files/users/{}".format(user_id)
    dimensions = [height, width]
    fileBytes = BytesIO(image)
    image = Image.open(fileBytes)

    format = image.format
    contentType = image.get_format_mimetype()
    original_width, original_height = image.size
    key_format = format.lower()

    if format in ["JPG", "JPEG"]:
        key_format = "jpg"
        filesToDelete = [
            {"Key": "{}/avatar.png".format(keyPath)},
            {"Key": "{}/avatar.gif".format(keyPath)},
        ]
    elif format == "PNG":
        filesToDelete = [
            {"Key": "{}/avatar.jpg".format(keyPath)},
            {"Key": "{}/avatar.gif".format(keyPath)},
        ]
    elif format == "GIF":
        filesToDelete = [
            {"Key": "{}/avatar.jpg".format(keyPath)},
            {"Key": "{}/avatar.png".format(keyPath)},
        ]

    key = "{}/avatar.{}".format(keyPath, key_format)

    if original_height == height and original_width == width:
        try:
            return upload_image(key, filesToDelete, contentType, image)
        except Exception as e:
            print("Upload image error:", e)
            return {
                "success": False,
                "message": "There was an error uploading your file.",
            }
    else:
        try:
            if format.lower() in ["jpg", "jpeg", "png"]:
                image = resize_image(image, dimensions)
                imgByteArr = save_image(image, format=format)
            elif format.lower() == "gif":
                loop = image.info.get("loop", 0)
                frames, duration_info = resize_gif(image, dimensions)
                imgByteArr = save_image(
                    frames[0],
                    format=format,
                    save_all=True,
                    optimize=True,
                    append_images=frames[1:],
                    duration=duration_info,
                    loop=loop,
                )
        except Exception as e:
            print("Save image:", e)
            return {
                "success": False,
                "message": "There was an error resizing and compressing your file.",
            }

        try:
            return upload_image(key, filesToDelete, contentType, imgByteArr)
        except Exception as e:
            print("Upload image error:", e)
            return {
                "success": False,
                "message": "There was an error uploading your file.",
            }
