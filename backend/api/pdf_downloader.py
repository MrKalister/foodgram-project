import io

from django.http import FileResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from foodgram.settings import FONTS_FILES_DIR


def create_pdf_file(shopping_cart):
    pdfmetrics.registerFont(
        TTFont('Helvetica', FONTS_FILES_DIR, 'UTF-8')
    )
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter, bottomup=0)
    pdf.translate(cm, cm)
    pdf.setFont('Helvetica', 22)
    pdf.drawString(200, 5, 'Список покупок:')
    pdf.setFont('Helvetica', 16)
    down_param = 20
    for number, ingredient in enumerate(shopping_cart, start=1):
        pdf.drawString(
            10,
            down_param,
            f"{number}. {ingredient['ingredient__name']}, "
            f"{ingredient['ingredient_amount_sum']} "
            f"{ingredient['ingredient__measurement_unit']}.",
        )
        down_param += 20
        if down_param >= 780:
            down_param = 20
            pdf.showPage()
            pdf.setFont('Helvetica', 16)
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename='shopping_cart.pdf'
    )
