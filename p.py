import openai
from weasyprint import HTML

# Set up your OpenAI API key
client = openai.OpenAI(api_key="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")

def read_club_info(file_path):
    """Read club information from a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_html_poster(club_info):
    """Generate HTML poster using OpenAI API with a local prompt."""
    prompt = f"""
    You are an expert in advertising and web design. Create a visually engaging HTML structure for a club poster 
    based on the following information:

    {club_info}

    The HTML should:
    - Include a catchy title and tagline at the top.
    - Use semantic HTML tags (e.g., <h1>, <p>, <ul>, <li>) for proper structure.
    - Highlight the club's activities, benefits, meeting details, and contact information.
    - Add placeholders for styling (e.g., classes like 'title', 'content', 'activities').
    - Keep the layout professional, clean, and ready to convert to a styled PDF.

    Return only the HTML code, without any additional explanations.
    """
    response = client.chat.completions.create(
        model="gpt-4",  # Use "gpt-4" if you have access
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def convert_html_to_pdf(html_content, output_pdf):
    """Convert the generated HTML to a styled PDF."""
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
    HTML(string=styled_html).write_pdf(output_pdf)

def main():
    # Input and output file paths
    input_file = "club_info.txt"  # Replace with your text file name
    output_pdf = "poster.pdf"

    # Read club information
    club_info = read_club_info(input_file)

    # Generate HTML poster using local prompt
    html_poster = generate_html_poster(club_info)

    # Convert HTML to styled PDF
    convert_html_to_pdf(html_poster, output_pdf)

    print(f"Styled poster PDF has been saved to {output_pdf}")

if __name__ == "__main__":
    main()