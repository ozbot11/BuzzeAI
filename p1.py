import os
import openai
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration
import logging

# Load environment variables
from dotenv import load_dotenv
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

# OpenAI API setup
client = openai.OpenAI(api_key="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")

def read_club_info(file_path: str) -> dict:
    """
    Read club information from a .txt file.
    The file should follow a key-value structure:
    Name: Example Club
    Mission: To promote learning.
    Purpose: Bring like-minded people together.
    Audience: Students who love to learn.
    """
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

def generate_content(club_info: dict, document_type: str) -> str:
    """
    Generate document content using OpenAI API.
    """
    prompt = f"""
    Create a visually striking and creative {document_type} for the following club:
    Name: {club_info.get('name', 'N/A')}
    Mission: {club_info.get('mission', 'N/A')}
    Purpose: {club_info.get('purpose', 'N/A')}
    Intended Audience: {club_info.get('audience', 'N/A')}

    Use HTML and CSS for complete control over the document's appearance. Be creative and artistic in your design!
    Consider using these elements:
    - Background colors or gradients for different sections
    - Creative typography with varying font sizes and styles
    - Icons or minimal graphics to represent key points
    - Appropriate margins for a professional look

    Sections to include:
    1. Eye-catching title/header
    2. Brief introduction
    3. Mission statement
    4. Key benefits of joining
    5. Upcoming events or activities
    6. How to join
    7. Contact information

    Format your response as a complete HTML document with embedded CSS.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating content: {str(e)}")
        raise

def create_pdf(content: str, filename: str, margins: str = "1cm"):
    """
    Create a PDF from the HTML content using WeasyPrint.
    """
    css = CSS(string=f"""
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Montserrat:wght@400;700&display=swap');
        @page {{
            margin: {margins};
        }}
        body {{
            font-family: 'Roboto', sans-serif;
            margin: 0;
            padding: 0;
        }}
        h1, h2 {{
            font-family: 'Montserrat', sans-serif;
        }}
    """, font_config=FontConfiguration())

    try:
        HTML(string=content).write_pdf(filename, stylesheets=[css])
        logging.info(f"PDF created successfully: {filename}")
    except Exception as e:
        logging.error(f"Error creating PDF: {str(e)}")
        raise

def main():
    # Input file path for club info and output PDF file
    input_file = "club_info.txt"  # Replace with your text file
    output_pdf = "club_poster.pdf"

    # Read club information from the text file
    logging.info("Reading club information from file...")
    club_info = read_club_info(input_file)

    # Generate HTML content
    logging.info("Generating HTML content...")
    html_content = generate_content(club_info, "poster")

    # Generate PDF from the HTML content
    logging.info("Creating PDF from HTML content...")
    create_pdf(html_content, output_pdf)

    logging.info(f"Process complete. PDF saved as {output_pdf}")

if __name__ == "__main__":
    main()