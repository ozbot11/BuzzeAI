import openai
from openai import OpenAI
import os

client = openai.OpenAI(api_key="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")
# client = OpenAI()

def read_club_info(file_path):
    """Read club information from a text file."""
    with open(file_path, 'r') as file:
        return file.read()

def generate_poster_text(club_info):
    """Generate poster text using OpenAI API."""
    prompt = (
        "You are an expert in creating engaging posters. Based on the following club information, "
        "create an exciting and concise text for a poster to attract new members:\n\n"
        f"{club_info}\n\n"
        "Make it eye-catching, include a call-to-action, and format it neatly for a poster."
    )
    response = client.chat.completions.create(
        # engine="text-davinci-003",  # Choose the model you prefer
        # engine="chatgpt-4o-latest",
        # prompt=prompt,
        # max_tokens=300,
        # temperature=0.7
        model="chatgpt-4o-latest",  # Use "gpt-4" if you have access
        messages=[
                    {"role": "system", "content": "You are a professional document creator for clubs and organizations."},
                    {"role": "user", "content": prompt}
                ],
        max_tokens=300,
        temperature=0.7
    )
    return response.choices[0].text.strip()

def save_poster(file_path, content):
    """Save the generated poster text to a file."""
    with open(file_path, 'w') as file:
        file.write(content)

def main():
    # Input and output file paths
    input_file = "club_info.txt"  # Replace with your text file name
    output_file = "poster.txt"

    # Read club information
    club_info = read_club_info(input_file)

    # Generate poster text
    poster_text = generate_poster_text(club_info)

    # Save the poster text to a file
    save_poster(output_file, poster_text)

    print(f"Poster text has been saved to {output_file}")

if __name__ == "__main__":
    main()

# import os
# import openai
# from openai import AsyncOpenAI
# from typing import Dict, List, Tuple
# from pydantic import BaseModel
# import fastapi
# from fastapi import FastAPI, HTTPException, BackgroundTasks
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import FileResponse
# from fastapi.responses import JSONResponse
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib.units import inch
# from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
# from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
# from docx import Document
# from docx.shared import Inches, Pt, RGBColor
# from docx.enum.text import WD_ALIGN_PARAGRAPH
# import asyncio
# import logging
# from dotenv import load_dotenv
# from fastapi.responses import FileResponse
# from weasyprint import HTML, CSS
# from weasyprint.fonts import FontConfiguration
# from bs4 import BeautifulSoup
# from PyPDF2 import PdfReader

# load_dotenv()

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.FileHandler("app.log"),  # Logs to a file
#         logging.StreamHandler()  # Logs to the console
#     ]
# )
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Advanced Club Document Generator")
# app.mount("/static", StaticFiles(directory="."), name="static")

# @app.get("/")
# async def read_index():
#     return FileResponse('index.html')

# @app.exception_handler(HTTPException)
# async def http_exception_handler(request, exc):
#     logging.error(f"HTTPException: {exc.detail}")
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={"detail": exc.detail, "custom_message": "An error occurred during document generation."},
#     )

# # OpenAI API setup
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Models
# class ClubInfo(BaseModel):
#     name: str
#     mission: str
#     purpose: str
#     audience: str
#     logo_url: str = None

# class DocumentRequest(BaseModel):
#     club_info: ClubInfo
#     document_type: str
#     output_format: str
#     margins: str = '0'  # Default to no margins

# def load_all_pdf_templates(template_dir='pdf_templates'):
#     templates = {}
#     for filename in os.listdir(template_dir):
#         if filename.endswith('.pdf'):
#             file_path = os.path.join(template_dir, filename)
#             reader = PdfReader(file_path)
#             content = ""
#             for page in reader.pages:
#                 content += page.extract_text()
#             templates[filename] = content
#     return templates
# # Document generation functions
# async def generate_content(club_info: Dict, document_type: str) -> str:
#     templates = load_all_pdf_templates()
    
#     template_content = "\n\n".join(templates.values())
#     prompt = f"""
#     Create a visually striking and creative {document_type} for the following club:
#     Name: {club_info['name']}
#     Mission: {club_info['mission']}
#     Purpose: {club_info['purpose']}
#     Intended Audience: {club_info['audience']}

#     Use the following templates as inspiration for creating a {document_type} for the club.

#     {template_content}

#     Use HTML and CSS for complete control over the document's appearance. Be creative and artistic in your design! It will be rendered by the Weasyprint library.

#     Consider using these elements to enhance the visual appeal:
#     - Dividing lines to separate sections (use <hr> tags with custom styles)
#     - Background colors or gradients for different sections
#     - Creative typography with varying font sizes and styles
#     - Icons or emojis to represent key points (use Unicode characters)
#     - Text boxes or callouts for important information

#     Include the following sections, but feel free to arrange them creatively:
#     1. Eye-catching title/header
#     2. Brief introduction
#     3. Mission statement
#     4. Key benefits of joining
#     5. Upcoming events or activities
#     6. How to join
#     7. Contact information

#     If asked to generate a document like a poster or flyer, please ensure that you don't structure it like a document but have very unconventional placement. You don't have to convey every single piece of information given, just cover the parts that prospective members/participants would want to see.

#     Use your artistic license to make the poster visually engaging and unique. Don't hesitate to use bold colors, interesting layouts, or unconventional design elements. However, only use info given to you. Also do not include every single piece of info if making a document such as a poster (which is constrained to one page single sided) as this would take too much space. Any taglines should be very short and brief. please make sure to consider spacing between different elements, and have appropriate spacing.

#     I don't want too many failure points, so try to implement the best 20% of ideas that will yield 80% of the impact.

#     Depending on the type of document you are generating, the following CSS and JavaScript to ensure content fits on one page and scales dynamically:
# <style> @page {{ size: letter; margin: 0; }} body {{ width: 100vw; height: 100vh; margin: 0; padding: 1cm; box-sizing: border-box; overflow: hidden; }} .content {{ width: 100%; height: 100%; overflow: hidden; }} </style> <script> function scaleContent() {{ var content = document.querySelector('.content'); var scaleX = document.body.clientWidth / content.offsetWidth; var scaleY = document.body.clientHeight / content.offsetHeight; var scale = Math.min(scaleX, scaleY); content.style.transform = `scale(${{scale}})`; content.style.transformOrigin = 'top left'; }} window.onload = scaleContent; window.onresize = scaleContent; </script>

#     Format your response as a complete HTML document with embedded CSS.
#     Format your response as a complete HTML document with embedded CSS.
#     Use the following CSS to ensure content fits on one page:
#     <style>
#     @page {{ size: letter; margin: 0; }}
#     body {{ width: 100%; height: 100vh; margin: 0; padding: 1cm; box-sizing: border-box; overflow: hidden; }}
#     .content {{ max-height: 100%; overflow: auto; }}
#     </style>
#     Wrap your main content in a div with the 'content' class.
#     Add the following JavaScript to scale content if it exceeds the page height:
#     <script>
#     window.onload = function() {{
#         var content = document.querySelector('.content');
#         var scale = 1;
#         while (content.scrollHeight > content.clientHeight && scale > 0.7) {{
#             scale -= 0.05;
#             content.style.transform = `scale(${{scale}})`;
#             content.style.transformOrigin = 'top left';
#         }}
#     }}
#     </script>
#     """

#     max_retries = 3
#     for attempt in range(max_retries):
#         try:
#             response = client.chat.completions.create(
#                 model="chatgpt-4o-latest",
#                 messages=[
#                     {"role": "system", "content": "You are a professional document creator for clubs and organizations."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=2000
#             )
#             out = response.choices[0].message.content
#             out = out.split("```")[1][4:]
#             print(out)
#             return out
#         except Exception as e:
#             logger.error(f"Error in API call: {type(e).__name__}: {str(e)}")
#             if attempt == max_retries - 1:
#                 logger.error(f"Failed to generate content after {max_retries} attempts")
#                 raise HTTPException(status_code=500, detail="Failed to generate document content")
#             await asyncio.sleep(2 ** attempt)

# def create_pdf(content: str, club_info: Dict, filename: str, margins: str = '0'):
#     # Define default styles with customizable margins
#     default_css = CSS(string=f'''
#         @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Montserrat:wght@400;700&display=swap');
#         @page {{ margin: {margins}; size: letter; }}
#         body {{ font-family: 'Roboto', sans-serif; margin: 0; padding: 0; }}
#         h1, h2, h3 {{ font-family: 'Montserrat', sans-serif; }}
#     ''')

#     # Create FontConfiguration
#     font_config = FontConfiguration()

#     # Generate PDF
#     HTML(string=content).write_pdf(
#         filename,
#         stylesheets=[default_css],
#         font_config=font_config
#     )

# def create_docx(content: str, club_info: Dict, filename: str):
#     doc = Document()
#     soup = BeautifulSoup(content, 'html.parser')
    
#     for element in soup.find_all(['h1', 'h2', 'p', 'div', 'span']):
#         p = doc.add_paragraph()
#         run = p.add_run(element.text)
        
#         if 'style' in element.attrs:
#             style = element['style']
            
#             if 'font-size' in style:
#                 size = style.split('font-size:')[1].split('pt').strip()
#                 run.font.size = Pt(int(float(size)))
                
#             if 'color' in style:
#                 color = style.split('color:')[1].split(';').strip()
#                 run.font.color.rgb = RGBColor.from_string(color.lstrip('#'))
                
#             if 'font-weight' in style and 'bold' in style:
#                 run.bold = True
                
#     doc.save(filename)

# # API route
# @app.post("/generate-document")
# async def create_document(request: DocumentRequest, background_tasks: BackgroundTasks, margins: str = '0'):
#     try:
#         logging.info(f"Generating document for club: {request.club_info.name}")
        
#         content = await generate_content(request.club_info.dict(), request.document_type)
        
#         file_name = f"{request.club_info.name}_{request.document_type}"
        
#         if request.output_format == "pdf":
#             file_name += ".pdf"
#             create_pdf(content, request.club_info.dict(), file_name, margins)
            
#         elif request.output_format == "docx":
#             file_name += ".docx"
#             create_docx(content, request.club_info.dict(), file_name)
            
#         else:
#             raise HTTPException(status_code=400, detail="Unsupported output format")
        
#         logging.info(f"Document generated: {file_name}")
        
#         download_link = f"/download/{file_name}"
        
#         return {"message": f"Document generated successfully", "download_link": download_link}
        
#     except Exception as e:
#         logging.error(f"Error in document generation: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Document generation failed: {str(e)}")

# # Root route
# @app.get("/")
# def root():
#     return {"message": "Welcome to the Advanced Club Document Generator API"}

# @app.get("/download/{filename}")
# async def download_file(filename: str):
#     file_path = f"./{filename}"
    
#     if os.path.exists(file_path):
#         return FileResponse(file_path, filename=filename, media_type='application/octet-stream')
    
#     return {"error": "File not found"}