from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_pdf(quote_details, filename):
    c = canvas.Canvas(filename, pagesize=A4)
    # Add content to PDF
    c.drawString(100, 750, "Quote: " + quote_details)
    c.save()