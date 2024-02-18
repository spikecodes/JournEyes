from google.cloud import storage
from dotenv import load_dotenv
import os
import uuid
import serpapi
from openai import OpenAI
import base64


load_dotenv()


def upload_blob(bucket_name, base64_data, destination_blob_name):
    """Uploads base64 encoded data to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Decode the base64 string to bytes
    image_data = base64.b64decode(base64_data)

    # Use upload_from_string to upload the data
    blob.upload_from_string(image_data)

    print(f"Data uploaded to {destination_blob_name}.")


def identify_object(lst):
    client = OpenAI()
    system_prompt = "Your task is to identify the most common and specific subject in a given list of image titles, sorted in non-decreasing order of priority. Return the result in the format {title: <title>, object: <object>}, where <title> is the most specific name of the subject directly from the list, and <object> is the general category or type of the item. Prioritize earlier items in the list for determining the most common subject. Ensure specificity in identification, applicable to various subjects like technology, food, or other categories. For example, if the most common subject is 'Nikon D850', the response should be {title: 'Nikon D850', object: 'camera'}."
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f"List: {lst}",
            },
        ],
    )

    return completion.choices[0].message.content


def google_lens_search(base64_image: str):
    """Reverse Google image search."""
    api_key = os.getenv("SERPAPI_API_KEY")
    file_id = str(uuid.uuid4())
    bucket_name = "treehacks24-vr"
    upload_blob(bucket_name, base64_image, file_id)

    image_url = f"https://storage.googleapis.com/{bucket_name}/{file_id}"
    print(image_url)

    params = {
        "engine": "google_lens",
        "url": image_url,
        "api_key": os.getenv("SERPAPI_API_KEY"),
    }

    search = serpapi.search(params)
    visual_matches = search["visual_matches"]
    titles = [match["title"] for match in visual_matches if "title" in match]
    print(titles)
    res = identify_object(titles)
    print(res)
    return res


def convert_to_base64(image_path: str):
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
    image_base64 = base64.b64encode(image_data)
    image_base64_str = image_base64.decode("utf-8")
    return image_base64_str


image_base64 = convert_to_base64("test.HEIC")

google_lens_search(image_base64)
