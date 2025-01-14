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
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def generate_content(club_info: dict, document_type: str) -> str:
    """Generate document content using OpenAI API."""
    prompt = f"""
    Create a visually striking and creative {document_type} for the following club:
    Name: {club_info['name']}
    Mission: {club_info['mission']}
    Purpose: {club_info['purpose']}
    Intended Audience: {club_info['audience']}

    Design Instructions:
    - Ensure the poster content fits entirely on a single page (8.5 x 11 inches).
    - Use a grid layout to organize content evenly across the page.
    - Include sections:
        1. Club Name (bold and centered).
        2. Tagline or Mission Statement.
        3. Key Benefits of Joining.
        4. Upcoming Events or Activities.
        5. Contact Information.
    - Use spacing, font sizes, and margins that prevent overlapping.
    - Make the poster colorful and visually appealing with a modern design.
    - Include clear boundaries between sections with padding or dividing lines.

    Output a complete HTML document with embedded CSS. Ensure the content fits within one page and is well-aligned.
    """
    try:
        response = client.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating content: {str(e)}")
        raise

def create_pdf(content: str, filename: str):
    """Create a PDF from the HTML content using WeasyPrint."""
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
        }}
        .poster {{
            display: grid;
            grid-template-rows: auto 1fr auto;
            grid-gap: 20px;
            padding: 20px;
            height: 100%;
            box-sizing: border-box;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }}
        h1 {{
            font-size: 30px;
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
            margin: 0;
            padding: 0;
            list-style-type: disc;
        }}
        ul li {{
            margin-left: 20px;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .section {{
            padding: 10px;
            border-radius: 8px;
            background: #f9f9f9;
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