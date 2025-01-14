import os
import openai
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration
import logging
from dotenv import load_dotenv

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

# OpenAI API setup
client = openai.OpenAI(api_key="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")

def read_club_info(file_path: str) -> dict:
    """
    Read club information from a .txt file.
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
    Name: {club_info['name']}
    Mission: {club_info['mission']}
    Purpose: {club_info['purpose']}
    Intended Audience: {club_info['audience']}

    Use HTML and CSS for complete control over the document's appearance. Be creative and artistic in your design! It will be rendered by the Weasyprint library version 52.

    Design Instructions:
    - Ensure the poster content fits on a single page (letter size: 8.5 x 11 inches).
    - Use bold, eye-catching titles, and modern, readable fonts.
    - Include sections for:
        1. Club Name and Tagline
        2. Mission Statement
        3. Key Benefits of Joining
        4. Upcoming Events or Activities
        5. Contact Information
    - Use spacing, alignment, and scaling techniques to avoid overflow while maintaining visual appeal.
    - Incorporate background gradients, rounded corners, and shadows for a professional look.
    - Scale text sizes, margins, and element placements dynamically to ensure everything fits neatly within the page.

    Output a complete HTML document with embedded CSS. The content must not exceed one page.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating content: {str(e)}")
        raise

def create_pdf(content: str, filename: str):
    """
    Create a PDF from the HTML content using WeasyPrint.
    """
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
            background: linear-gradient(to bottom right, #f9f9f9, #e8e8e8);
            color: #333;
        }}
        .poster {{
            max-width: 8.5in;
            max-height: 11in;
            margin: auto;
            padding: 20px;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }}
        h1 {{
            font-family: 'Montserrat', sans-serif;
            font-size: 28px;
            font-weight: 700;
            text-align: center;
            color: #007BFF;
            margin-bottom: 10px;
        }}
        h2 {{
            font-size: 20px;
            font-weight: 600;
            color: #444;
            margin-bottom: 10px;
            border-bottom: 2px solid #007BFF;
            display: inline-block;
        }}
        p {{
            font-size: 14px;
            line-height: 1.5;
            color: #555;
        }}
        .section {{
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background: #fdfdfd;
        }}
        ul {{
            padding-left: 20px;
        }}
        ul li {{
            font-size: 14px;
            color: #333;
            margin-bottom: 8px;
        }}
        .footer {{
            text-align: center;
            font-size: 12px;
            color: #666;
        }}
    """)

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