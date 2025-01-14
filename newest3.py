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
import weasyprint
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

def generate_content(club_info: dict, document_type: str, templates: dict, image_folder: str, image: str) -> list:
    """
    Generate three versions of HTML content using OpenAI API, incorporating templates.
    """
    template_content = "\n\n".join(templates.values())

    prompt = f"""
    Create three visually striking and creative versions of a {document_type} for the following club:
    Name: {club_info['name']}
    Mission: {club_info['mission']}
    Purpose: {club_info['purpose']}
    Intended Audience: {club_info['audience']}

    Use the following templates as examples of basic designs:
    {template_content}

    Each version should:
    - Exceed the quality of the provided templates
    - Incorporate a cohesive color theme, effective use of borders, and layout design
    - Use an image from the folder '{image_folder}' in a way that enhances the design

    From this folder, take the image named {image}.jpg. Make sure to incorporate this in your html and finalized poster.    

    Format your response as three complete HTML documents, separated by "---VERSION---" markers. Do not include any additional text or explanations outside the HTML structure.

        Use HTML and CSS for complete control over the document's appearance. Be creative and artistic in your design! It will be rendered by the Weasyprint library.

    Consider using these elements to enhance the visual appeal:
    - Dividing lines to separate sections (use <hr> tags with custom styles)
    - Background colors or gradients for different sections
    - Creative typography with varying font sizes and styles
    - Icons or emojis to represent key points (use Unicode characters)
    - Text boxes or callouts for important information

    Include the following sections, but feel free to arrange them creatively:
    1. Eye-catching title/header
    2. Brief introduction
    3. Mission statement
    4. Key benefits of joining
    5. Upcoming events or activities
    6. How to join
    7. Contact information

    If asked to generate a document like a poster or flyer, please ensure that you don't structure it like a document but have very unconventional placement. You don't have to convey every single piece of information given, just cover the parts that prospective members/participants would want to see.

    Use your artistic license to make the poster visually engaging and unique. Don't hesitate to use bold colors, interesting layouts, or unconventional design elements. However, only use info given to you. Also do not include every single piece of info if making a document such as a poster (which is constrained to one page single sided) as this would take too much space. Any taglines should be very short and brief. please make sure to consider spacing between different elements, and have appropriate spacing.

    I don't want too many failure points, so try to implement the best 20% of ideas that will yield 80% of the impact.

    Below is the HTML as an example for how to implement an image into your poster in a way that looks nice:
    <!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Image and Text Integration</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 20px;
            }}

            .content {{
                max-width: 800px;
                margin: 0 auto;
            }}

            .text-image-container {{
                display: flex;
                align-items: center;
                gap: 20px;
            }}

            .text-image-container img {{
                max-width: 40%;
                height: auto;
                border-radius: 8px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            }}

            .text-image-container .text {{
                flex: 1;
            }}

            .text-image-container.reverse {{
            flex-direction: row-reverse;
            }}

            @media (max-width: 600px) {{
                .text-image-container {{
                    flex-direction: column;
                    text-align: center;
            }}

            .text-image-container img {{
                max-width: 80%;
            }}
        }}
    </style>
    </head>
    <body>
    <div class="content">
        <h1>Enhancing Your Content with Images</h1>
        <div class="text-image-container">
        <img src="example-image.jpg" alt="A beautiful landscape">
        <div class="text">
            <p>
            Images are a great way to make your content more engaging. This is an example of how you can align text and images
            side-by-side for a clean and professional look. The image is responsive, ensuring it scales appropriately on smaller devices.
            </p>
        </div>
        </div>
        <div class="text-image-container reverse">
        <img src="example-image-2.jpg" alt="A scenic cityscape">
        <div class="text">
            <p>
            For variety, you can reverse the layout, placing the image on the opposite side of the text. This helps maintain a balanced
            design throughout your content and keeps the reader visually interested.
            </p>
        </div>
        </div>
    </div>
    </body>
    </html>
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional document creator."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            n=1,
            
        )
        raw_output = response.choices[0].message.content.strip()
        versions = raw_output.split("---VERSION---")
        return [version.strip() for version in versions if version.strip()]
    except Exception as e:
        logging.error(f"Error generating content: {e}")
        raise

def html_center(html: str):
    prompt = f"""
        You are a graphic designer tasked with making sure that posters are always properly fitting the 8.5 in by 11 in page that they are on. To do so, you must make sure the html for the poster is set up to make the poster fill out the full page in both width and height. Below is some code to use in accomplishing this goal:

        <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Perfect Scaling</title>
                <style>
                    body {{
                        margin: 0;
                        padding: 0;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background-color: #f0f0f0;
                    }}

                    .page {{
                        width: 8.5in;
                        height: 11in;
                        background: white;
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        overflow: hidden;
                        position: relative;
                    }}

                    .content {{
                        padding: 1in;
                        box-sizing: border-box;
                    }}
                </style>
            </head>
            <body>
                <div class="page" id="page">
                    <div class="content">
                        <h1>Your Content Here</h1>
                        <p>Add more content to test perfect scaling for both height and width.</p>
                        <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
                        <p>Ut ac quam id nunc placerat fringilla ut id eros.</p>
                    </div>
                </div>

                <script>
                    window.onload = function() {{
                        var page = document.getElementById('page');
                        var content = page.querySelector('.content');
                        
                        // Get dimensions of the page and content
                        var pageWidth = page.offsetWidth;
                        var pageHeight = page.offsetHeight;
                        var contentWidth = content.scrollWidth;
                        var contentHeight = content.scrollHeight;

                        // Calculate scale factors for both width and height
                        var widthScale = pageWidth / contentWidth;
                        var heightScale = pageHeight / contentHeight;

                        // Use the smaller scale to ensure the content fits within both dimensions
                        var scale = Math.min(widthScale, heightScale);

                        // Apply scaling
                        content.style.transform = `scale(${{scale}})`;
                        content.style.transformOrigin = 'top left';
                    }}
                </script>
            </body>
            </html>
    """
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a professional document creator."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000
    )
    return

def extract_pdf_content(file_path):
    """Extract text content from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text_content = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text_content
    except Exception as e:
        logging.error(f"Error extracting content from {file_path}: {e}")
        return ""

def evaluate_posters_with_gpt(poster_files):
    """
    Use GPT to evaluate and rank posters based on their content and structure.

    :param poster_files: List of paths to the poster PDF files.
    :return: Name of the best poster.
    """
    try:
        # Extract content from each poster
        posters_content = {file: extract_pdf_content(file) for file in poster_files}

        # Construct prompt for GPT
        prompt = """
        You are a graphic design and content evaluation expert.
        The following are the extracted contents from three posters. Your task is to analyze and determine which poster is the best based on the following criteria:
        - Visual appeal (if inferred from text descriptions)
        - Organization and clarity of content
        - Overall effectiveness in delivering its message

        Rank the posters from best to worst and provide a brief explanation for your choice.

        Give a poster 5 points for having the following structure:
        {{
            "Title": "<Poster Title>",
            "Style": {{
                "Background": ["<Color>", "<Gradient>"]
            }},
            "Sections": [
                {{
                    "Title": "<SectionTitle>",
                    "Style": {{
                        "Border": ["<Color>", "<Outline>"]
                    }},
                    "Contents": [
                        {{
                            "Text": "<Information>",
                        }},
                    ],
                }}
            ],
        }}

        Take away a point for each missing element.

        Then, give it an extra 3 points if it incorporates an image.

        Now, rank the posters based on their point totals.

        Poster 1:
        {poster1_content}

        Poster 2:
        {poster2_content}

        Poster 3:
        {poster3_content}

        Provide your response as:
        1. Best Poster: Poster X (with a brief explanation)
        2. Second Best: Poster Y (with a brief explanation)
        3. Third Best: Poster Z (with a brief explanation)
        """.format(
            poster1_content=posters_content[poster_files[0]],
            poster2_content=posters_content[poster_files[1]],
            poster3_content=posters_content[poster_files[2]]
        )

        # Call OpenAI GPT API
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )

        # Parse and return the response
        evaluation = response.choices[0].message.content.strip()
        return evaluation

    except Exception as e:
        logging.error(f"Error evaluating posters with GPT: {e}")
        return "Error in evaluation."

# async def main():
#     # Input file path for club info and output files
#     input_file = "club_info.txt"
#     html_output_pdfs = ["club_poster_html_1.pdf", "club_poster_html_2.pdf", "club_poster_html_3.pdf"]
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

#     # Generate HTML content and create HTML-based PDFs
#     logging.info("Generating HTML content...")
#     html_versions = generate_content(club_info, "poster", assets["templates"], image_folder)

#     for html_content in html_versions:
#         version = 0
#         with open("poster.html", "w") as html_file:
#             html_file.write(html_content)
#         logging.info("Creating HTML-based PDF...")
#         HTML(string=html_content).write_pdf(html_output_pdfs[version])
#         version = version + 1

#     logging.info(f"Process complete. HTML-based PDFs: {html_output_pdfs}")

async def main():
    # Input file path for club info and output files
    input_file = "club_info.txt"
    html_output_pdfs = ["club_poster_html_1.pdf", "club_poster_html_2.pdf", "club_poster_html_3.pdf"]
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

    # Generate HTML content and create HTML-based PDFs
    logging.info("Generating HTML content...")
    html_versions = generate_content(club_info, "poster", assets["templates"], image_folder, selected_image)

    # Iterate over the versions and save them as separate PDFs
    for i, html_content in enumerate(html_versions):
        try:
            output_pdf = html_output_pdfs[i]
            adjusted_output_pdf = html_center(output_pdf)
            logging.info(f"Creating HTML-based PDF {i + 1}...")
            # HTML(string=html_content).write_pdf(output_pdf)
            HTML(string=html_content).write_pdf(adjusted_output_pdf)
        except IndexError:
            logging.error(f"Not enough output filenames provided for HTML versions. Skipping version {i + 1}.")
        except Exception as e:
            logging.error(f"Error generating HTML-based PDF {i + 1}: {e}")

    result = evaluate_posters_with_gpt(html_output_pdfs)
    print(result)

    logging.info(f"Process complete. HTML-based PDFs: {html_output_pdfs}, LaTeX-based PDF: {latex_output_pdf}")

if __name__ == "__main__":
    asyncio.run(main())