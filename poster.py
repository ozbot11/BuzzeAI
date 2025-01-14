import openai
from weasyprint import HTML

# Set up your OpenAI API key
client = openai.OpenAI(api_key="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")

def read_club_info(file_path):
    """Read club information from a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_html_poster(club_info):
    """Generate HTML poster using OpenAI API."""
    messages = [
        {"role": "system", "content": (
            "You are a creative advertising expert and web designer. Your task is to create an engaging, visually structured, and "
            "professionally formatted HTML code for a club poster. The HTML should include headings, subheadings, and sections like "
            "a catchy title, description, activities list, meeting details, and contact information."
        )},
        {"role": "user", "content": (
            f"Based on the following club information, generate a complete HTML structure for a poster:\n\n"
            f"{club_info}\n\n"
            "The HTML should:\n"
            "- Include proper semantic tags (e.g., <h1>, <p>, <ul>, <li>).\n"
            "- Have placeholders for styling (e.g., classes like 'title', 'content', etc.).\n"
            "- Be clean and well-organized for easy conversion to a PDF.\n"
            "- Provide engaging and concise text for each section."
        )}
    ]
    response = client.chat.completions.create(
        model="gpt-4",  # Use "gpt-4" if you have access
        messages=messages,
        max_tokens=800,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def convert_html_to_pdf(html_content, output_pdf):
    """Convert the generated HTML to a styled PDF."""
    # Define a CSS stylesheet for the PDF
    css = """
    body {
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        background-color: #f9f9f9;
        color: #333;
    }
    .poster {
        max-width: 800px;
        margin: 40px auto;
        padding: 20px;
        background: #fff;
        border: 1px solid #ddd;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border-radius: 10px;
    }
    .title {
        text-align: center;
        font-size: 28px;
        font-weight: bold;
        color: #007BFF;
        margin-bottom: 20px;
    }
    .content {
        font-size: 16px;
        line-height: 1.6;
    }
    ul {
        margin: 10px 0;
        padding: 0 20px;
    }
    li {
        margin: 5px 0;
    }
    .footer {
        text-align: center;
        margin-top: 20px;
        font-size: 14px;
        color: #666;
    }
    """
    # Wrap the HTML content in a <div> for styling
    styled_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>{css}</style>
    </head>
    <body>
        <div class="poster">
            {html_content}
        </div>
    </body>
    </html>
    """
    # Generate PDF
    HTML(string=styled_html).write_pdf(output_pdf)

def main():
    # Input and output file paths
    input_file = "club_info.txt"  # Replace with your text file name
    output_pdf = "poster.pdf"

    # Read club information
    club_info = read_club_info(input_file)

    # Generate HTML poster
    html_poster = generate_html_poster(club_info)

    # Convert HTML to styled PDF
    convert_html_to_pdf(html_poster, output_pdf)

    print(f"Styled poster PDF has been saved to {output_pdf}")

if __name__ == "__main__":
    main()