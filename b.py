from PIL import Image, ImageDraw, ImageFont

# Create a blank image with white background
width, height = 800, 1000
poster = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(poster)

# Load fonts (substitute with appropriate paths to .ttf files)
try:
    font_large = ImageFont.truetype("arialbd.ttf", 70)
    font_medium = ImageFont.truetype("arialbd.ttf", 50)
    font_small = ImageFont.truetype("arial.ttf", 30)
except:
    # Fallback to default font
    font_large = font_medium = font_small = ImageFont.load_default()

# Draw the "Community Health Fair" title
draw.text((50, 50), "Community", fill="#40BFC1", font=font_medium)
draw.text((50, 130), "HEALTH", fill="black", font=font_large)
draw.text((50, 230), "FAIR", fill="black", font=font_large)

# Add the placeholder for the logo
logo_size = 120
logo_position = (600, 60)
draw.ellipse([logo_position, (logo_position[0] + logo_size, logo_position[1] + logo_size)], fill="black")
draw.text((logo_position[0] + 10, logo_position[1] + 40), "YOUR\nLOGO\nHERE", fill="white", font=font_small, align="center")

# Draw the date and time section
draw.rectangle([50, 300, width - 50, 380], fill="#40BFC1")
draw.text((100, 320), "SATURDAY, SEPTEMBER 23RD FROM 9AM TO 2PM", fill="white", font=font_small)

# Add "Take care of your health" section
draw.text((50, 400), "TAKE CARE\nOF YOUR HEALTH", fill="black", font=font_medium)
draw.text((50, 500), "KNOW YOUR NUMBERS", fill="#40BFC1", font=font_medium)
draw.text((50, 580), "2596 Tacco Rd Atlanta Ga 30596", fill="black", font=font_small)

# Add "Free Health Screening" section
draw.text((50, 650), "Free Health Screening", fill="black", font=font_medium)
services = ["Blood Pressure", "Cholesterol", "Nutrition Assessment", "Bone Density"]
for i, service in enumerate(services):
    draw.text((50, 720 + i * 50), f"\u2713 {service}", fill="#40BFC1", font=font_small)

# Add the "Join us!" text
draw.text((width - 200, height - 100), "Join us!", fill="black", font=font_medium)

# Save or display the poster
poster.show()
poster.save("health_fair_poster.png")