import openai
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Set up your OpenAI API key
client = openai.OpenAI(api_key="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")

def read_club_info(file_path):
    """Read club information from a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_poster_text(club_info):
    """Generate poster text using OpenAI API."""
    # Using the chat completion API
    messages = [
        {"role": "system", "content": (
            "You are an expert in graphic design and advertising. Your task is to create highly engaging and attractive "
            "posters. Use catchy language, clear formatting, and a strong call-to-action to attract maximum attention."
        )},
        {"role": "user", "content": (
            f"Based on the following club information, create a detailed and visually engaging poster text:\n\n"
            f"{club_info}\n\n"
            "Include a compelling tagline, highlight the club's key features, mention meeting details, and provide "
            "contact information clearly. Make it inspiring and persuasive to motivate new members to join."
        )}
    ]
    # response = openai.ChatCompletion.create(
    #     model="gpt-3.5-turbo",  # Use "gpt-4" if you have access
    #     messages=messages,
    #     max_tokens=500,
    #     temperature=0.8
    # )

    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=messages,
        max_tokens=300,
        temperature=0.7
    )
    # Access the message content
    return response.choices[0].message.content.strip()

def save_poster_to_pdf(file_path, content):
    """Save the generated poster text to a PDF file."""
    # Set up the canvas
    c = canvas.Canvas(file_path, pagesize=letter)
    width, height = letter

    # Define title and margins
    title = "Club Poster"
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 50, title)

    # Add content with wrapping
    c.setFont("Helvetica", 12)
    text = c.beginText(50, height - 100)
    text.setTextOrigin(50, height - 100)
    text.setFont("Helvetica", 12)
    for line in content.split("\n"):
        text.textLine(line.strip())
    c.drawText(text)

    # Save the PDF
    c.save()

def main():
    # Input and output file paths
    input_file = "club_info.txt"  # Replace with your text file name
    output_pdf = "poster.pdf"

    # Read club information
    club_info = read_club_info(input_file)

    # Generate poster text
    poster_text = generate_poster_text(club_info)

    # Save the poster text to a PDF
    save_poster_to_pdf(output_pdf, poster_text)

    print(f"Poster PDF has been saved to {output_pdf}")

if __name__ == "__main__":
    main()