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

#     # # Generate LaTeX-based PDF
#     # logging.info("Creating PDF with LaTeX...")
#     # create_pdf_latex(club_info, selected_image, latex_output_pdf)

#     # logging.info(f"Process complete. HTML-based PDF: {html_output_pdf}, LaTeX-based PDF: {latex_output_pdf}")

#     generated_content_latex = generate_content_latex(club_info)
#     save_content_to_file(generated_content_latex, "latex.txt")

# if __name__ == "__main__":
#     asyncio.run(main())



from openai import OpenAI
import os
import base64

# def encode_image(image_path):
#     with open(image_path, "rb") as image_file:
#         return base64.b64encode(image_file.read()).decode('utf-8')

def generate_content_latex(club_info: dict):
    base_prompt = f"""
    Create a visually striking and creative poster for the following club:
    Name: {club_info['name']}
    Mission: {club_info['mission']}
    Purpose: {club_info['purpose']}
    Intended Audience: {club_info['audience']}

    General Guidelines:
    1. Ensure the content aligns with the club's mission and purpose.
    2. Tailor the language to appeal to the target audience.
    3. Highlight the club's unique features.
    4. Incorporate the location and contact information strategically.
    5. Address the additional details provided.
    6. Consider the visual hierarchy and flow of information.
    7. Use font styles, sizes, and colors to enhance readability and impact.
    8. Place key information prominently for maximum effectiveness.
    """

    # if image_paths:
    #     base_prompt += "\nIncorporate references to the following images in your content:\n"
    #     for i, path in enumerate(image_paths, 1):
    #         base_prompt += f"Image {i}: {os.path.basename(path)}\n"
    base_prompt += """
    Create a visually striking poster design. Consider the following:
    - Use a bold, large font for the main title to grab attention.
    - Employ a color scheme that reflects the club's identity and the event's theme.
    - Strategically place the most important information (e.g., event name, date, location) in the top third of the poster.
    - Use varying font sizes to create a clear hierarchy of information.
    - Incorporate white space effectively to avoid cluttering.
    - Ensure high contrast between text and background for readability.
    - Use graphic elements or icons to visually represent key aspects of the event.
    
    # OUTPUT FORMAT:
    # Provide your response in the following LaTeX format:
    
    # \\documentclass[whatever class you want goes here}
    # \\usepackage{graphicx}
    # \\usepackage{color}
    # \\any more packages you need to include
    
    # \\begin{document}
    
    # [Your poster content here, using pdfLaTeX commands for formatting, specifying fonts, sizes, colors, and placement]
    
    # \\end{document}
    
    # Make your designs simplistic but they should look good.
    # Include comments explaining your design choices and their intended impact.
    # """
    # elif content_type == "newsletter":
    #     base_prompt += """
    #     Design a comprehensive newsletter. Consider the following:
    #     - Use a clear, readable font for the body text (e.g., serif for print, sans-serif for digital).
    #     - Create an eye-catching header with the club's name and newsletter title.
    #     - Use color to highlight section headers and important information.
    #     - Maintain consistent formatting throughout for a professional look.
    #     - Use columns to organize information effectively.
    #     - Include pull quotes or highlighted text boxes to emphasize key points.
    #     - Ensure proper spacing between sections for easy navigation.
        
    #     OUTPUT FORMAT:
    #     Provide your response in the following LaTeX format:
        
    #     \\documentclass[11pt]{article}
    #     \\usepackage{graphicx}
    #     \\usepackage{color}
    #     \\usepackage{multicol}
    #     \\usepackage{fontspec}
        
    #     \\begin{document}
        
    #     [Your newsletter content here, using pdfLaTeX commands for formatting, specifying fonts, sizes, colors, and layout]
        
    #     \\end{document}
        
    #     Include comments explaining your design choices and their intended impact.
    #     """
    # elif content_type == "social media post":
    #     base_prompt += """
    #     Craft an engaging social media post. Consider the following:
    #     - Start with a strong, attention-grabbing headline or question.
    #     - Use emojis strategically to add visual interest and convey tone.
    #     - Keep the main content concise and impactful (ideal length varies by platform).
    #     - Use line breaks effectively to improve readability.
    #     - Include a clear and compelling call-to-action.
    #     - Use relevant and trending hashtags to increase visibility.
    #     - Consider the tone and language that best resonate with your target audience.
        
    #     OUTPUT FORMAT:
    #     Provide your response as plain text, formatted as follows:
        
    #     [Attention-grabbing headline or question]
        
    #     [Main post content with strategic use of emojis and line breaks]
        
    #     [Call to action]
        
    #     #Hashtag1 #Hashtag2 #Hashtag3
        
    #     Explain your choices for headline, content structure, emojis, and hashtags.
    #     """
    # elif content_type == "event description":
    #     base_prompt += """
    #     Write a detailed event description. Consider the following:
    #     - Create a compelling and descriptive event title.
    #     - Use subheadings to break up the text and highlight key information.
    #     - Start with a brief, engaging summary of the event.
    #     - Use bullet points for easy scanning of important details.
    #     - Include a section on "Why Attend" to highlight the value proposition.
    #     - Use action-oriented language to encourage registration.
    #     - Ensure all crucial information (date, time, location, how to register) is prominently displayed.
        
    #     OUTPUT FORMAT:
    #     Provide your response as plain text, formatted as follows:
        
    #     EVENT TITLE
        
    #     [Brief, engaging summary]
        
    #     Date: [Date]
    #     Time: [Time]
    #     Location: [Location]
        
    #     About the Event:
    #     [Detailed event description]
        
    #     Why Attend:
    #     • [Reason 1]
    #     • [Reason 2]
    #     • [Reason 3]
        
    #     What to Expect:
    #     • [Point 1]
    #     • [Point 2]
    #     • [Point 3]
        
    #     How to Register: [Registration information]
        
    #     Contact: [Contact information]
        
    #     Explain your choices for title, structure, and language used to maximize impact and clarity.
    #     """

    messages = [
        {"role": "system", "content": "You are an expert in creating promotional content for clubs and organizations, with a deep understanding of effective design principles, typography, and marketing strategies."},
        {"role": "user", "content": base_prompt}
    ]

    # if image_paths:
    #     for path in image_paths:
    #         base64_image = encode_image(path)
    #         messages.append({
    #             "role": "user",
    #             "content": [
    #                 {
    #                     "type": "image_url",
    #                     "image_url": {
    #                         "url": f"data:image/png;base64,{base64_image}"
    #                     }
    #                 }
    #             ]
    #         })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=2500
    )

    return response.choices[0].message.content.strip()

def save_content_to_file(content, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(content)

# # Main program with hardcoded inputs
# if _name_ == "_main_":
#     # Hardcoded club profile
#     club_profile = {
#         'name': "EcoTech Innovators",
#         'mission': "To foster innovation in sustainable technology and promote eco-friendly solutions",
#         'purpose': "Bringing together students and professionals to develop and share green tech ideas",
#         'audience': "University students and young professionals interested in sustainability and technology",
#         'size': "150 active members",
#         'meeting_frequency': "Weekly, every Tuesday at 7 PM",
#         'location': "Green Innovation Center, University of Washington",
#         'contact_info': "info@ecotechinnovators.com, (555) 123-4567"
#     }

#     # Hardcoded content details and image paths
#     content_details = {
#         'poster': "Advertising our annual sustainability hackathon 'Code Green 2025' on March 15-17, 2025, at Kane Hall 120, University of Washington. Grand prize of $10,000.",
#         'newsletter': "Monthly update for September 2024, featuring our upcoming guest lecture series and recent project successes",
#         'social media post': "Promoting our weekly meetup on Biomimicry in Sustainable Design, happening next Tuesday",
#         'event description': "Detailed information about our upcoming 5th Annual EcoTech Conference on November 12-14, 2024"
#     }

#     image_paths = {
#         'poster': "C:\\Users\\rache\\Downloads\\ClubAI-main\\ClubAI-main\\clubai\\buzzbuilder\\buzzbuilder\\ai\\hackathon.png",
#         'newsletter': "C:\\Users\\rache\\Downloads\\ClubAI-main\\ClubAI-main\\clubai\\buzzbuilder\\buzzbuilder\\ai\\hackathon.png"
#     }

    # # Generate and save content for each type
    # for content_type, details in content_details.items():
    #     print(f"\nGenerating {content_type}...")
    #     image_path = image_paths.get(content_type)
    #     generated_content = generate_content(
    #         club_profile, 
    #         content_type, 
    #         details, 
    #         [image_path] if image_path else None
    #     )

    #     filename = f"{content_type.replace(' ', '_')}_content.txt"
    #     save_content_to_file(generated_content, filename)
    #     print(f"Content saved to {filename}")

    #     # Print the generated content
    #     print(f"\nGenerated {content_type.capitalize()} Content:")
    #     print("="*50)
    #     print(generated_content)
    #     print("="*50)

    # print("\nAll content has been generated and saved to separate files.")



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

    # # Generate LaTeX-based PDF
    # logging.info("Creating PDF with LaTeX...")
    # create_pdf_latex(club_info, selected_image, latex_output_pdf)

    # logging.info(f"Process complete. HTML-based PDF: {html_output_pdf}, LaTeX-based PDF: {latex_output_pdf}")

    generated_content_latex = generate_content_latex(club_info)
    save_content_to_file(generated_content_latex, "latex.txt")

if __name__ == "__main__":
    asyncio.run(main())