import openai
import os

# Set up your OpenAI API key
# openai.api_key = "your_openai_api_key_here"  # Replace with your actual API key

client = openai.OpenAI(api_key="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")

def read_club_info(file_path):
    """Read club information from a text file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def generate_poster_text(club_info):
    """Generate poster text using OpenAI API."""
    # Using the chat completion API
    messages = [
        {"role": "system", "content": "You are an expert in creating engaging posters."},
        {"role": "user", "content": (
            f"Based on the following club information, create an exciting and concise text for a poster to attract new members:\n\n"
            f"{club_info}\n\n"
            "Make it eye-catching, include a call-to-action, and format it neatly for a poster."
        )}
    ]
    response = client.chat.completions.create(
        model="chatgpt-4o-latest",
        messages=messages,
        max_tokens=300,
        temperature=0.7
    )
    # Access the message content
    return response.choices[0].message.content.strip()

def save_poster(file_path, content):
    """Save the generated poster text to a file."""
    with open(file_path, 'w', encoding='utf-8') as file:
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
