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
    # """Generate document content using OpenAI API."""
    # prompt = f"""
    # Create a visually striking and creative {document_type} for the following club:
    # Name: {club_info['name']}
    # Mission: {club_info['mission']}
    # Purpose: {club_info['purpose']}
    # Intended Audience: {club_info['audience']}

    # Design Instructions:
    # - Ensure the poster content fits entirely on a single page (8.5 x 11 inches).
    # - Use a grid layout to organize content evenly across the page.
    # - Include sections:
    #     1. Club Name (bold and centered).
    #     2. Tagline or Mission Statement.
    #     3. Key Benefits of Joining.
    #     4. Upcoming Events or Activities.
    #     5. Contact Information.
    # - Use spacing, font sizes, and margins that prevent overlapping.
    # - Make the poster colorful and visually appealing with a modern design.
    # - Include clear boundaries between sections with padding or dividing lines.

    # Output a complete HTML document with embedded CSS. Ensure the content fits within one page and is well-aligned.
    # """
    # try:
    #     response = client.chat.completions.create(
    #         model="chatgpt-4o-latest",
    #         messages=[{"role": "user", "content": prompt}],
    #         max_tokens=2000,
    #         temperature=0.8
    #     )
    #     return response.choices[0].message.content.strip()
    # except Exception as e:
    #     logging.error(f"Error generating content: {str(e)}")
    #     raise

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

    Depending on the type of document you are generating, the following CSS and JavaScript to ensure content fits on one page and scales dynamically:
<style> @page {{ size: letter; margin: 0; }} body {{ width: 100vw; height: 100vh; margin: 0; padding: 1cm; box-sizing: border-box; overflow: hidden; }} .content {{ width: 100%; height: 100%; overflow: hidden; }} </style> <script> function scaleContent() {{ var content = document.querySelector('.content'); var scaleX = document.body.clientWidth / content.offsetWidth; var scaleY = document.body.clientHeight / content.offsetHeight; var scale = Math.min(scaleX, scaleY); content.style.transform = `scale(${{scale}})`; content.style.transformOrigin = 'top left'; }} window.onload = scaleContent; window.onresize = scaleContent; </script>

    Format your response as a complete HTML document with embedded CSS.
    Format your response as a complete HTML document with embedded CSS.
    Use the following CSS to ensure content fits on one page:
    <style>
    @page {{ size: letter; margin: 0; }}
    body {{ width: 100%; height: 100vh; margin: 0; padding: 1cm; box-sizing: border-box; overflow: hidden; }}
    .content {{ max-height: 100%; overflow: auto; }}
    </style>
    Wrap your main content in a div with the 'content' class.
    Add the following JavaScript to scale content if it exceeds the page height:
    <script>
    window.onload = function() {{
        var content = document.querySelector('.content');
        var scale = 1;
        while (content.scrollHeight > content.clientHeight && scale > 0.7) {{
            scale -= 0.05;
            content.style.transform = `scale(${{scale}})`;
            content.style.transformOrigin = 'top left';
        }}
    }}
    </script>
    """

    max_retries = 3
    for attempt in range(max_retries):
        # try:
            response = client.chat.completions.create(
                model="chatgpt-4o-latest",
                messages=[
                    {"role": "system", "content": "You are a professional document creator for clubs and organizations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000
            )
            out = response.choices[0].message.content
            out = out.split("```")[1][4:]
            print(out)
        #     return out
        # except Exception as e:
        #     logger.error(f"Error in API call: {type(e).__name__}: {str(e)}")
        #     if attempt == max_retries - 1:
        #         logger.error(f"Failed to generate content after {max_retries} attempts")
        #         raise HTTPException(status_code=500, detail="Failed to generate document content")
        #     await asyncio.sleep(2 ** attempt)

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