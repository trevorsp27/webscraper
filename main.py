import os
import requests
from bs4 import BeautifulSoup
import urllib.request
from urllib.parse import urljoin
from google.cloud import vision
import time

# Initialize Google Vision API client
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"GOOGLE_VISION_API_KEY"
client = vision.ImageAnnotatorClient()

# Variables to change
prompt = 'dog'
number_of_images = 16

# Function to check image relevance using Google Vision API
def check_image_relevance(image_path, prompt):
    try:
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.label_detection(image=image)
        labels = response.label_annotations
        label_descriptions = [label.description for label in labels]
        if any(keyword in ' '.join(label_descriptions).lower() for keyword in prompt.split()):
            print(f"Labels for image {image_path}: {label_descriptions}")
            return True
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
    return False

# Function to download image
def download_image(url, folder_path=r'C:\Users\tspin\Desktop\CyberGuard\images_for_research'):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    img_name = os.path.join(folder_path, url.split('/')[-1].split('?')[0])  # Remove query parameters if any
    try:
        urllib.request.urlretrieve(url, img_name)
        return img_name
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None

# Function to scrape a webpage
def scrape_page(url, prompt, number_of_images):
    response = requests.get(url, verify=False)
    soup = BeautifulSoup(response.content, 'html.parser')
    images = soup.find_all('img')
    image_count = 0
    relevant_images_found = 0
    for img in images:
        if relevant_images_found >= number_of_images:
            break
        img_url = img.get('src')
        if img_url:
            # Convert relative URL to absolute URL
            img_url = urljoin(url, img_url)
            img_path = download_image(img_url)
            if img_path:
                if check_image_relevance(img_path, prompt):
                    relevant_images_found += 1
                    print(f"Relevant image found: {img_path}")
                else:
                    os.remove(img_path)
                    print(f"Deleted non-relevant image: {img_path}")
                image_count += 1
            if image_count >= number_of_images and relevant_images_found == 0:
                print("First images are not relevant, moving to the next URL.")
                break

# Function to get initial URLs using ChatGPT API
def get_initial_urls(prompt):
    api_url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer GPT_API_KEY",
        "Content-Type": "application/json"
    }
    api_prompt = f"Provide 5 URLs that might contain images of {prompt}."
    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": api_prompt}]
    }
    
    response = requests.post(api_url, headers=headers, json=data)
    
    if response.status_code == 200:
        content = response.json()["choices"][0]["message"]["content"]
        print(f"OpenAI API response content: {content}")
        
        # Initialize an empty list to store the URLs
        initial_urls = []
        
        # Split the content into lines and iterate over each line
        for line in content.split('\n'):
            line = line[3:]
            initial_urls.append(line)
        
        return initial_urls
    else:
        print(f"Failed to get URLs: {response.status_code} {response.text}")
        return []

# Get initial URLs based on the prompt
initial_urls = get_initial_urls(prompt)
print(f"Initial URLs: {initial_urls}")

# Scrape each initial URL
for url in initial_urls:
    print(f"Scraping {url}")
    scrape_page(url, prompt, number_of_images)
    time.sleep(2)  # Adding a small delay to avoid potential rate limits or bans