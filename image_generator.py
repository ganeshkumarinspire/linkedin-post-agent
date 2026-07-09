import os
import requests
from openai import OpenAI
from pathlib import Path

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def generate_image(prompt: str, output_path: str = "post_image.png") -> str:
    """Generate an image with DALL-E 3 and save it locally. Returns the file path."""
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    image_data = requests.get(image_url, timeout=30).content

    Path(output_path).write_bytes(image_data)
    print(f"Image saved to {output_path}")
    return output_path


if __name__ == "__main__":
    test_prompt = (
        "Minimalist illustration of a lone developer looking at a whiteboard covered "
        "in sticky notes, soft blue and white tones, professional, no text in image"
    )
    generate_image(test_prompt, "test_image.png")
