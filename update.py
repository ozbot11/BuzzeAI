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
from weasyprint import HTML

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
                elif file.endswith('.html'):
                    html_path = os.path.join(root, file)
                    with open(html_path, 'r', encoding='utf-8') as html_file:
                        templates[file] = html_file.read()
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

def generate_content(club_info: dict, document_type: str, templates: dict, image_folder: str) -> str:
    """
    Generate HTML content using OpenAI API, incorporating templates.
    """
    template_content = "\n\n".join(templates.values())

    prompt = f"""
    Create a visually striking and creative {document_type} for the following club:
    Name: {club_info['name']}
    Mission: {club_info['mission']}
    Purpose: {club_info['purpose']}
    Intended Audience: {club_info['audience']}

    Use the following templates as examples of basic designs:
    {template_content}

    The new design should exceed the quality of the provided templates and incorporate a cohesive color theme, effective use of borders, and layout design.
    Additionally, an image from the folder '{image_folder}' is available for use. You may use it in a way that enhances the poster design.

    Format your response as a complete HTML document with embedded CSS. Do not include any additional text or explanations.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional document creator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        raw_output = response.choices[0].message.content.strip()
        return raw_output
    except Exception as e:
        logging.error(f"Error generating content: {e}")
        raise

def create_pdf_latex(club_info: dict, image: str, filename: str):
    """Create a PDF using LaTeX."""
    try:
        latex_content = f"""
        \\documentclass[12pt]{{article}}
        \\usepackage{{graphicx}}
        \\usepackage[margin=1in]{{geometry}}
        \\begin{{document}}
        \\begin{{center}}
        \\textbf{{\\Huge {club_info['name']}}} \\
        \\vspace{{0.5in}}
        \\includegraphics[width=0.8\\textwidth]{{{image}}} \\
        \\vspace{{0.5in}}
        \\textbf{{\\Large Mission Statement:}} \\
        {club_info.get('mission', '')} \\
        \\vspace{{0.25in}}
        \\textbf{{\\Large Purpose:}} \\
        {club_info.get('purpose', '')} \\
        \vspace{{0.25in}}
        \\textbf{{\\Large Intended Audience:}} \\
        {club_info.get('audience', '')}
        \\end{{center}}
        \\end{{document}}
        """
        with open("poster.tex", "w") as tex_file:
            tex_file.write(latex_content)
        os.system(f"pdflatex -output-directory=. poster.tex")
        os.rename("poster.pdf", filename)
        logging.info(f"PDF created successfully with LaTeX: {filename}")
    except Exception as e:
        logging.error(f"Error creating LaTeX PDF: {e}")
        raise

async def main():
    # Input file path for club info and output files
    input_file = "club_info.txt"
    html_output_pdf = "club_poster_html.pdf"
    latex_output_pdf = "club_poster_latex.pdf"
    template_dir = "templates"  # Directory containing templates
    image_folder = "images"  # Folder to store downloaded images

    # Read club information
    logging.info("Reading club information from file...")
    club_info = read_club_info(input_file)

    # Load templates and ads
    logging.info("Loading templates and ads...")
    assets = load_templates_and_ads(template_dir)

    # Extract keywords and search for images
    logging.info("Extracting keywords and searching for images...")
    keywords = extract_keywords(club_info)
    selected_image = search_unsplash(keywords, image_folder)

    # Generate HTML content and create HTML-based PDF
    logging.info("Generating HTML content...")
    html_content = generate_content(club_info, "poster", assets["templates"], image_folder)
    with open("poster.html", "w") as html_file:
        html_file.write(html_content)
    logging.info("Creating HTML-based PDF...")
    HTML(string=html_content).write_pdf(html_output_pdf)

    # Generate LaTeX-based PDF
    logging.info("Creating PDF with LaTeX...")
    create_pdf_latex(club_info, selected_image, latex_output_pdf)

    logging.info(f"Process complete. HTML-based PDF: {html_output_pdf}, LaTeX-based PDF: {latex_output_pdf}")

if __name__ == "__main__":
    asyncio.run(main())

# async def main():
#     # Input file path for club info and output files
#     input_file = "club_info.txt"
#     html_output_pdf = "club_poster_html.pdf"
#     latex_output_pdf = "club_poster_latex.pdf"
#     template_dir = "templates"  # Directory containing templates
#     image_folder = "images"  # Folder to store downloaded images

#     # Read club information
#     logging.info("Reading club information from file...")
#     club_info = read_club_info(input_file)

#     # Load templates and ads
#     logging.info("Loading templates and ads...")
#     assets = load_templates_and_ads(template_dir)

#     # Extract keywords and search for images
#     logging.info("Extracting keywords and searching for images...")
#     keywords = extract_keywords(club_info)
#     selected_image = search_unsplash(keywords, image_folder)

#     # Generate HTML content and create HTML-based PDF
#     logging.info("Generating HTML content...")
#     html_content = generate_content(club_info, "poster", assets["templates"], image_folder)
#     with open("poster.html", "w") as html_file:
#         html_file.write(html_content)
#     logging.info("Creating HTML-based PDF...")
#     HTML(string=html_content).write_pdf(html_output_pdf)

#     # Generate LaTeX-based PDF
#     logging.info("Creating PDF with LaTeX...")
#     create_pdf_latex(club_info, selected_image, latex_output_pdf)

#     logging.info(f"Process complete. HTML-based PDF: {html_output_pdf}, LaTeX-based PDF: {latex_output_pdf}")

if __name__ == "__main__":
    asyncio.run(main())