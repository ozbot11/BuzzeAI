import os
import openai
import requests
from weasyprint import HTML, CSS
import logging
from dotenv import load_dotenv
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

def search_unsplash(keywords: list, output_folder: str, per_page: int = 5) -> None:
    """
    Search Unsplash for images based on keywords and save them to the output folder.
    """
    base_url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}

    os.makedirs(output_folder, exist_ok=True)

    try:
        for keyword in keywords:
            params = {"query": keyword, "per_page": per_page}
            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                results = response.json()["results"]
                for idx, result in enumerate(results):
                    image_url = result["urls"]["regular"]
                    image_data = requests.get(image_url).content
                    with open(os.path.join(output_folder, f"{keyword}_{idx + 1}.jpg"), 'wb') as img_file:
                        img_file.write(image_data)
            else:
                logging.error(f"Unsplash API error for keyword '{keyword}': {response.status_code}")
    except Exception as e:
        logging.error(f"Error searching Unsplash: {e}")

# def extract_html(raw_output: str) -> str:
#     """Extract valid HTML content from the API's response."""
#     try:
#         start_index = raw_output.find("<!DOCTYPE html>")
#         if start_index == -1:
#             raise ValueError("HTML content not found in the response.")
#         end_index = raw_output.rfind("</html>") + len("</html>")
#         if end_index == -1:
#             raise ValueError("HTML closing tag not found in the response.")
#         return raw_output[start_index:end_index]
#     except Exception as e:
#         logging.error(f"Error extracting HTML: {e}")
#         raise

# def extract_html(raw_output: str) -> str:
#     """Extract valid HTML content from the API's response."""
#     try:
#         start_index = raw_output.find("<!DOCTYPE html>")
#         if start_index == -1:
#             logging.error(f"HTML content not found. Raw output: {raw_output}")
#             raise ValueError("HTML content not found in the response.")
#         end_index = raw_output.rfind("</html>") + len("</html>")
#         if end_index == -1:
#             logging.warning("HTML closing tag not found, attempting partial extraction.")
#             end_index = len(raw_output)
#         return raw_output[start_index:end_index]
#     except Exception as e:
#         logging.error(f"Error extracting HTML: {e}")
#         raise

def extract_html(raw_output: str) -> str:
    """Extract valid HTML content from the API's response."""
    try:
        # Look for the starting tag of HTML
        start_index = raw_output.find("<!DOCTYPE html>")
        if start_index == -1:
            logging.warning("HTML start tag not found. Attempting regex extraction.")
            # Use regex to locate <html> content as a fallback
            match = re.search(r"(<html>.*?</html>)", raw_output, re.DOTALL)
            if match:
                return match.group(1)
            raise ValueError("HTML content not found in the response.")

        # Look for the ending tag of HTML
        end_index = raw_output.rfind("</html>") + len("</html>")
        if end_index == -1:
            logging.warning("HTML end tag not found. Assuming the rest of the content is HTML.")
            end_index = len(raw_output)

        # Return the extracted HTML content
        return raw_output[start_index:end_index]
    except Exception as e:
        logging.error(f"Error extracting HTML: {e}")
        raise

# def generate_content(club_info: dict, document_type: str, templates: dict, ads: list, image_folder: str) -> str:
#     """
#     Generate document content using OpenAI API, incorporating templates and ads.
#     """
#     template_content = "\n\n".join(templates.values())
#     ad_example_count = min(3, len(ads))  # Use up to 3 ad examples in the prompt
#     ad_examples = ads[:ad_example_count]

#     prompt = f"""
#     Create a visually striking and creative {document_type} for the following club:
#     Name: {club_info['name']}
#     Mission: {club_info['mission']}
#     Purpose: {club_info['purpose']}
#     Intended Audience: {club_info['audience']}

#     Use the following templates as inspiration for format and layout:
#     {template_content}

#     Additionally, consider the following ad examples as inspiration for incorporating images effectively:
#     {', '.join(ad_examples)}

#     Images from the folder '{image_folder}' have been downloaded based on relevant keywords. Use one or a few images as appropriate to enhance the design, but not all images need to be used.

#     Use HTML and CSS for complete control over the document's appearance. Ensure the output fits on a single page (8.5 x 11 inches). Be creative and artistic in your design!

#     Format your response as a complete HTML document with embedded CSS.
#     """
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4",
#             messages=[
#                 {"role": "system", "content": "You are a professional document creator for clubs and organizations."},
#                 {"role": "user", "content": prompt}
#             ],
#             max_tokens=2000
#         )
#         raw_output = response.choices[0].message.content.strip()
#         html_content = extract_html(raw_output)
#         return html_content
#     except Exception as e:
#         logging.error(f"Error generating content: {e}")
#         raise

def generate_content(club_info: dict, document_type: str, templates: dict, ads: list, image_folder: str) -> str:
    """
    Generate document content using OpenAI API, incorporating templates and ads.
    """
    template_content = "\n\n".join(templates.values())
    ad_example_count = min(3, len(ads))  # Use up to 3 ad examples in the prompt
    ad_examples = ads[:ad_example_count]

    prompt = f"""
    Create a visually striking and creative {document_type} for the following club:
    Name: {club_info['name']}
    Mission: {club_info['mission']}
    Purpose: {club_info['purpose']}
    Intended Audience: {club_info['audience']}

    Use the following templates as inspiration for format and layout:
    {template_content}

    Additionally, consider the following ad examples as inspiration for incorporating images effectively:
    {', '.join(ad_examples)}

    Images from the folder '{image_folder}' have been downloaded based on relevant keywords. Use one or a few images as appropriate to enhance the design, but not all images need to be used.

    Use HTML and CSS for complete control over the document's appearance. Ensure the output fits on a single page (8.5 x 11 inches). Be creative and artistic in your design!

    Format your response as a complete HTML document with embedded CSS. Do not include any text, explanations, or comments outside the HTML structure.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional document creator for clubs and organizations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000
        )
        raw_output = response.choices[0].message.content.strip()
        html_content = extract_html(raw_output)
        return html_content
    except Exception as e:
        logging.error(f"Error generating content: {e}")
        raise

def create_pdf(content: str, filename: str):
    """Create a PDF from the HTML content using WeasyPrint."""
    if not content:
        raise ValueError("HTML content is empty. Cannot create PDF.")
    
    css = CSS(string=f"""
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Montserrat:wght@400;700&display=swap');
        @page {{
            size: letter;
            margin: 1cm;
        }}
        body {{
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(to bottom, #ffffff, #f4f4f9);
            color: #333;
        }}
        .poster {{
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 20px;
            height: 100%;
            box-sizing: border-box;
            background: white;
            border-radius: 10px;
        }}
        h1 {{
            font-size: 32px;
            font-weight: bold;
            text-align: center;
            color: #007BFF;
        }}
        h2 {{
            font-size: 20px;
            font-weight: bold;
            color: #444;
            margin-bottom: 10px;
        }}
        p {{
            font-size: 14px;
            line-height: 1.5;
            text-align: justify;
        }}
        ul {{
            padding-left: 20px;
        }}
        ul li {{
            font-size: 14px;
            margin-bottom: 5px;
        }}
    """)

    try:
        HTML(string=content).write_pdf(filename, stylesheets=[css])
        logging.info(f"PDF created successfully: {filename}")
    except Exception as e:
        logging.error(f"Error creating PDF: {e}")
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
    search_unsplash(keywords, image_folder)

    # Generate HTML content
    logging.info("Generating HTML content...")
    html_content = generate_content(club_info, "poster", assets["templates"], assets["ads"], image_folder)

    # Generate PDF from the HTML content
    logging.info("Creating PDF from HTML content...")
    create_pdf(html_content, output_pdf)

    logging.info(f"Process complete. PDF saved as {output_pdf}")

if __name__ == "__main__":
    asyncio.run(main())