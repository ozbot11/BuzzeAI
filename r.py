import os
import openai
from weasyprint import HTML, CSS
import logging
from dotenv import load_dotenv
import asyncio

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
    """Generate document content using OpenAI API."""
    prompt = f"""
    Create a visually striking and creative {document_type} for the following club:
    Name: {club_info['name']}
    Mission: {club_info['mission']}
    Purpose: {club_info['purpose']}
    Intended Audience: {club_info['audience']}

    Use HTML and CSS for complete control over the document's appearance. Be creative and artistic in your design! It will be rendered by the WeasyPrint library.

    Format your response as a complete HTML document with embedded CSS that starts with <!DOCTYPE html> and no additional text or explanations.
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
        logging.error(f"Error creating PDF: {str(e)}")
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

    # Generate PDF from the HTML content
    logging.info("Creating PDF from HTML content...")
    create_pdf(html_content, output_pdf)

    logging.info(f"Process complete. PDF saved as {output_pdf}")

if __name__ == "__main__":
    asyncio.run(main())