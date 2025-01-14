import openai
from weasyprint import HTML

# Set up your OpenAI API key
client = openai.OpenAI(api_key="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")

def read_club_info(file_path):
    """Read club information from a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_poster_text(club_info):
    """Generate poster text using OpenAI API."""
    messages = [
        {"role": "system", "content": (
            "You are a creative advertising expert and graphic designer. Your task is to create detailed, structured, and engaging content "
            "for posters that inspire people to take action and join clubs. Use persuasive language and visually descriptive formatting."
        )},
        {"role": "user", "content": (
            f"Based on the following club information, create a detailed and engaging poster text:\n\n"
            f"{club_info}\n\n"
            "Format the content with:\n"
            "- A catchy title or tagline at the top.\n"
            "- A short and inspiring description of the club.\n"
            "- A bulleted list of key activities, benefits, or features.\n"
            "- Clearly highlighted meeting details and contact information.\n"
            "Make it inspiring, visually descriptive, and concise."
        )}
    ]
    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=messages,
        max_tokens=300,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def create_pdf_from_html(file_path, poster_content):
    """Generate a styled PDF poster from HTML using WeasyPrint."""
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background: #f9f9f9;
            }}
            .poster {{
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
                background: #fff;
                border: 2px solid #eee;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                border-radius: 8px;
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                color: #007BFF;
                margin-bottom: 20px;
            }}
            .content {{
                font-size: 16px;
                margin: 10px 0;
            }}
            ul {{
                margin: 10px 0 20px 20px;
                padding: 0;
                list-style-type: disc;
            }}
            li {{
                margin: 5px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                font-size: 14px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="poster">
            <div class="title">Welcome to Our Club!</div>
            <div class="content">
                {poster_content}
            </div>
            <div class="footer">Contact us for more details!</div>
        </div>
    </body>
    </html>
    """
    # Generate the PDF
    HTML(string=html_template).write_pdf(file_path)

def main():
    # Input and output file paths
    input_file = "club_info.txt"  # Replace with your text file name
    output_pdf = "poster.pdf"

    # Read club information
    club_info = read_club_info(input_file)

    # Generate poster text
    poster_text = generate_poster_text(club_info)

    # Generate PDF poster
    create_pdf_from_html(output_pdf, poster_text)

    print(f"Styled poster PDF has been saved to {output_pdf}")

if __name__ == "__main__":
    main()