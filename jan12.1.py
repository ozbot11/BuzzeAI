import os
import openai
import requests
from weasyprint import HTML, CSS
import logging
from dotenv import load_dotenv
import asyncio
import kagglehub

# Download latest version
path = kagglehub.dataset_download("groffo/ads16-dataset")

print("Path to dataset files:", path)

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

def extract_html(raw_output: str) -> str:
    """Extract valid HTML content from the API's response."""
    try:
        start_index = raw_output.find("<!DOCTYPE html>")
        if start_index == -1:
            raise ValueError("HTML content not found in the response.")
        end_index = raw_output.rfind("</html>") + len("</html>")
        if end_index == -1:
            raise ValueError("HTML closing tag not found in the response.")
        return raw_output[start_index:end_index]
    except Exception as e:
        logging.error(f"Error extracting HTML: {e}")
        raise

async def generate_content(club_info: dict, document_type: str) -> str:
    prompt = f"""
    Create a visually striking and creative {document_type} for the following club:
    Name: {club_info['name']}
    Mission: {club_info['mission']}
    Purpose: {club_info['purpose']}
    Intended Audience: {club_info['audience']}

    Use the following templates as inspiration for creating a {document_type} for the club.

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

    MAKE SURE THE GENERATED POSTER IS ONLY ONE PAGE.

    Format your response as a complete HTML document with embedded CSS.
    """
    max_retries = 3
    for attempt in range(max_retries):
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
            logging.error(f"Error in API call: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)

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

def search_unsplash(keywords: list, per_page: int = 5) -> list:
    """
    Search Unsplash for images based on keywords.
    """
    base_url = "https://api.unsplash.com/search/photos"
    headers = {"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"}
    images = []

    try:
        for keyword in keywords:
            params = {"query": keyword, "per_page": per_page}
            response = requests.get(base_url, headers=headers, params=params)
            if response.status_code == 200:
                results = response.json()["results"]
                images.extend([result["urls"]["regular"] for result in results])
            else:
                logging.error(f"Unsplash API error for keyword '{keyword}': {response.status_code}")
    except Exception as e:
        logging.error(f"Error searching Unsplash: {e}")

    return images

def get_club_images(club_info: dict) -> list:
    """
    Extract keywords from club info and search Unsplash for images.
    """
    logging.info("Extracting keywords from club info...")
    keywords = extract_keywords(club_info)
    logging.info(f"Keywords extracted: {keywords}")

    logging.info("Searching Unsplash for images...")
    images = search_unsplash(keywords)
    logging.info(f"Images found: {len(images)}")

    return images

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

    # Read club information from the text file
    logging.info("Reading club information from file...")
    club_info = read_club_info(input_file)

    # Generate HTML content
    logging.info("Generating HTML content...")
    html_content = await generate_content(club_info, "poster")

    # Find relevant images for the club
    logging.info("Finding images for the club...")
    images = get_club_images(club_info)
    logging.info(f"Found {len(images)} images.")

    # Generate PDF from the HTML content
    logging.info("Creating PDF from HTML content...")
    create_pdf(html_content, output_pdf)

    logging.info(f"Process complete. PDF saved as {output_pdf}")

if __name__ == "__main__":
    asyncio.run(main())