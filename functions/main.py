 Welcome to Cloud Functions for Firebase for Python!
# To get started, simply uncomment the below code or create your own.
# Deploy with `firebase deploy`

import tempfile
import os
import random

from firebase_functions import https_fn
from firebase_admin import initialize_app, storage

from PIL import Image, ImageEnhance
from io import BytesIO

initialize_app()

DESIRED_RESOLUTION = (640, 400)  # replace with your actual desired resolution


@https_fn.on_request()
def serve_image(req: https_fn.Request) -> https_fn.Response:
    filename = req.args.get("filename")
    
    image = convert_image(filename)

    if image is None:
        return https_fn.Response("File not found.", status=404)

    # Serve the image
    image_bytes = BytesIO()
    image.save(image_bytes, "JPEG")
    image_bytes.seek(0)
    return https_fn.Response(image_bytes, content_type="image/jpeg")


def convert_image(file_name):
    """Firebase function to convert images to the desired resolution and serve as non-progressive JPEGs."""

    bucket = storage.bucket()

    if file_name is None:
        print("No file name provided. Picking a random file.")
        # pick a file name from your bucket at random
        blobs = bucket.list_blobs(prefix="webgallery/")
        # remove results in webgallery/converted/
        pick = random.choice([blob.name for blob in blobs if not blob.name.startswith("webgallery/converted/") and not blob.name.endswith("/")])
        file_name = pick.split("/")[-1]

    file_path = f"webgallery/{file_name}"

    print(f"File selected: {file_name} ({file_path})...")

    # Skip if the file is not an image
    if not file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        print(f"Skipping non-image file: {file_name}")
        return

    # Check if the image has already been converted
    converted_blob = bucket.blob(f"webgallery/converted/{file_name}")
    if converted_blob.exists():
        print(f"Image {file_name} already converted. Returning the converted image.")
        
        # Read the converted image into a PIL Image
        converted_image_blob = bucket.blob(f"webgallery/converted/{file_name}")
        converted_image_bytes = converted_image_blob.download_as_bytes()
        converted_image = Image.open(BytesIO(converted_image_bytes))
        
        return converted_image

    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Download the image from Storage
    temp_file_path = os.path.join(temp_dir, file_name)
    blob = bucket.blob(file_path)
    blob.download_to_filename(temp_file_path)

    # Open the image with Pillow
    image = Image.open(temp_file_path)

    # thumbnail-ify image
    image.thumbnail(DESIRED_RESOLUTION)
    
    # use ImageEnhance to increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    brightness = ImageEnhance.Brightness(image)
    image = brightness.enhance(1.05)

    # Convert to non-progressive JPEG with the desired resolution
    new_im = Image.new("RGB", DESIRED_RESOLUTION, (0, 0, 0, 0))
    new_im.paste(image, ((DESIRED_RESOLUTION[0] - image.width) // 2, (DESIRED_RESOLUTION[1] - image.height) // 2))
    output_file_path = os.path.join(temp_dir, "converted_" + file_name)
    new_im.save(output_file_path, "JPEG", optimize=True, progressive=False)

    # Upload the converted image back to Storage
    output_blob = bucket.blob(f"webgallery/converted/{file_name}")
    output_blob.upload_from_filename(output_file_path)

    # Clean up temporary directory
    for file in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, file)
        os.unlink(file_path)
    os.rmdir(temp_dir)

    print(f"Image {file_name} converted and uploaded.")
    
    # Return the converted image
    return new_im
