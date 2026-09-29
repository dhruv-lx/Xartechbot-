import os
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from PIL import Image as PILImage
from config import EXPORTS_DIR, PHOTOS_DIR

def prepare_pdf_image(img_path, max_width=1.8*inch, max_height=1.8*inch):
    if not img_path or not os.path.exists(img_path):
        return None
    try:
        # Resize image cleanly to temporary thumbnail if needed
        thumb_dir = PHOTOS_DIR / "pdf_thumbs"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        filename = Path(img_path).name
        temp_img_path = thumb_dir / f"pdf_{filename}"
        
        with PILImage.open(img_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((300, 300), PILImage.Resampling.LANCZOS)
            img.save(temp_img_path, "JPEG", quality=85)
            
        return RLImage(str(temp_img_path), width=max_width, height=max_height)
    except Exception as e:
        print(f"Error preparing PDF image {img_path}: {e}")
        return None

def generate_pdf_report(visits, title="Xartech Client Visits Report", filter_info="All Records"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Xartech_Visits_{timestamp}.pdf"
    filepath = EXPORTS_DIR / filename
    
    doc = SimpleDocTemplate(
        str(filepath),
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#1E1B4B'),
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#475569')
    )
    
    val_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#0F172A')
    )
    
    shop_heading = ParagraphStyle(
        'ShopHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#4F46E5')
    )
    
    story = []
    
    # Header Section
    story.append(Paragraph("XARTECH CLIENT VISITS REPORT", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')} | Filter: {filter_info} | Total Visits: {len(visits)}", subtitle_style))
    story.append(Spacer(1, 10))
    
    if not visits:
        story.append(Paragraph("No client visits found for this report.", val_style))
    else:
        for idx, v in enumerate(visits, 1):
            shop_img = prepare_pdf_image(v.get('shop_photo_path'))
            card_img = prepare_pdf_image(v.get('card_photo_path'))
            
            # Left Column (Text info)
            info_data = [
                [Paragraph(f"#{v.get('id', idx)} - {v.get('shop_name', 'N/A')}", shop_heading), ""],
                [Paragraph("Owner:", label_style), Paragraph(v.get('owner_name') or "N/A", val_style)],
                [Paragraph("Phone:", label_style), Paragraph(v.get('phone_number', 'N/A'), val_style)],
                [Paragraph("Address:", label_style), Paragraph(v.get('address') or "GPS Location Recorded", val_style)],
                [Paragraph("Remarks:", label_style), Paragraph(v.get('remarks') or "None", val_style)],
                [Paragraph("Agent:", label_style), Paragraph(f"{v.get('agent_name', '')} (@{v.get('agent_username', '')})", val_style)],
                [Paragraph("Date/Time:", label_style), Paragraph(str(v.get('created_at', '')), val_style)],
            ]
            
            info_table = Table(info_data, colWidths=[1.0*inch, 2.5*inch])
            info_table.setStyle(TableStyle([
                ('SPAN', (0, 0), (1, 0)),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            
            # Images column
            img_elements = []
            if shop_img:
                img_elements.append(shop_img)
            else:
                img_elements.append(Paragraph("[No Shop Photo]", val_style))
                
            if card_img:
                img_elements.append(card_img)
            else:
                img_elements.append(Paragraph("[No Card Photo]", val_style))
                
            img_table = Table([[img_elements[0], img_elements[1]]], colWidths=[1.8*inch, 1.8*inch])
            img_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            # Main card table
            card_wrapper = Table([[info_table, img_table]], colWidths=[3.6*inch, 3.8*inch])
            card_wrapper.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
                ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
                ('ROUNDEDCORNERS', [6, 6, 6, 6]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('PADDING', (0, 0), (-1, -1), 8),
            ]))
            
            story.append(KeepTogether([card_wrapper, Spacer(1, 12)]))
            
    doc.build(story)
    return filepath
