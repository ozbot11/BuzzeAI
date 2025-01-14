import os
import openai
import requests
import logging
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import asyncio
from PyPDF2 import PdfReader
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# OpenAI and Unsplash API setup
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")

def read_club_info(file_path: str) -> dict:
    """Read club information from a .txt file."""
    club_info = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                if ":" in line:
                    key, value = line.split(":", 1)
                    club_info[key.strip().lower()] = value.strip()
    except Exception as e:
        logging.error(f"Error reading club info file: {e}")
        raise
    return club_info

def load_templates_and_ads(template_dir: str) -> dict:
    """Load templates and ad examples from the specified directory."""
    templates = {}
    ads = []

    try:
        for root, dirs, files in os.walk(template_dir):
            for file in files:
                if file.endswith('.pdf'):
                    pdf_path = os.path.join(root, file)
                    reader = PdfReader(pdf_path)
                    pdf_content = "".join(page.extract_text() for page in reader.pages)
                    templates[file] = pdf_content
                elif file.endswith(('.jpg', '.jpeg', '.png')):
                    ads.append(os.path.join(root, file))
    except Exception as e:
        logging.error(f"Error loading templates and ads: {e}")
        raise

    return {"templates": templates, "ads": ads}

def extract_keywords(club_info: dict) -> list:
    """
    Use GPT to extract relevant keywords from the club info for image search.
    """
    prompt = f"""
    Analyze the following club information and extract 5-10 keywords that describe the club visually:
    Name: {club_info.get('name', 'N/A')}
    Mission: {club_info.get('mission', 'N/A')}
    Purpose: {club_info.get('purpose', 'N/A')}
    Intended Audience: {club_info.get('audience', 'N/A')}

    The keywords should represent themes, objects, or activities that can be used to find relevant images for this club.
    Provide the keywords as a comma-separated list.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        raw_keywords = response.choices[0].message.content.strip()
        keywords = [keyword.strip() for keyword in raw_keywords.split(",")]
        return keywords
    except Exception as e:
        logging.error(f"Error extracting keywords: {e}")
        return []

def search_unsplash(keywords: list, output_folder: str) -> str:
    """
    Search Unsplash for images based on keywords and save the first image to the output folder.
    """
    base_url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    os.makedirs(output_folder, exist_ok=True)
    selected_image = None

    try:
        for keyword in keywords:
            params = {"query": keyword, "per_page": 1}
            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                results = response.json()["results"]
                if results:
                    image_url = results[0]["urls"]["regular"]
                    image_data = requests.get(image_url).content
                    selected_image = os.path.join(output_folder, f"{keyword}.jpg")
                    with open(selected_image, 'wb') as img_file:
                        img_file.write(image_data)
                    break
            else:
                logging.error(f"Unsplash API error for keyword '{keyword}': {response.status_code}")
    except Exception as e:
        logging.error(f"Error searching Unsplash: {e}")

    return selected_image

def create_pdf_reportlab(club_info: dict, image: str, filename: str):
    """Create a PDF from the club information and a single image using ReportLab."""
    try:
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            name="TitleStyle",
            fontSize=24,
            leading=28,
            alignment=1,
            textColor=colors.darkblue
        )
        section_style = ParagraphStyle(
            name="SectionStyle",
            fontSize=16,
            leading=20,
            spaceAfter=10,
            textColor=colors.darkgreen
        )
        body_style = ParagraphStyle(
            name="BodyStyle",
            fontSize=12,
            leading=15,
            textColor=colors.black
        )

        # Elements to add to the PDF
        elements = []
        elements.append(Paragraph(club_info['name'], title_style))
        elements.append(Spacer(1, 0.5 * inch))

        if 'mission' in club_info:
            elements.append(Paragraph("Mission Statement:", section_style))
            elements.append(Paragraph(club_info['mission'], body_style))
            elements.append(Spacer(1, 0.25 * inch))

        if 'purpose' in club_info:
            elements.append(Paragraph("Purpose:", section_style))
            elements.append(Paragraph(club_info['purpose'], body_style))
            elements.append(Spacer(1, 0.25 * inch))

        if 'audience' in club_info:
            elements.append(Paragraph("Intended Audience:", section_style))
            elements.append(Paragraph(club_info['audience'], body_style))
            elements.append(Spacer(1, 0.5 * inch))

        # Add the single image
        if image:
            elements.append(Image(image, width=5 * inch, height=3 * inch))
            elements.append(Spacer(1, 0.5 * inch))

        # Build PDF
        doc.build(elements)
        logging.info(f"PDF created successfully: {filename}")
    except Exception as e:
        logging.error(f"Error creating PDF with ReportLab: {e}")
        raise

async def main():
    # Input file path for club info and output PDF file
    input_file = "club_info.txt"  # Replace with your text file
    output_pdf = "club_poster.pdf"
    template_dir = "templates"  # Directory containing templates and ads
    image_folder = "images"  # Folder to store downloaded images

    # Read club information from the text file
    logging.info("Reading club information from file...")
    club_info = read_club_info(input_file)

    # Load templates and ad examples
    logging.info("Loading templates and ad examples...")
    assets = load_templates_and_ads(template_dir)

    # Extract keywords and search Unsplash for images
    logging.info("Extracting keywords and searching for images...")
    keywords = extract_keywords(club_info)
    selected_image = search_unsplash(keywords, image_folder)

    # Generate PDF from the club information and the selected image
    logging.info("Creating PDF with ReportLab...")
    create_pdf_reportlab(club_info, selected_image, output_pdf)

    logging.info(f"Process complete. PDF saved as {output_pdf}")

if __name__ == "__main__":
    asyncio.run(main())