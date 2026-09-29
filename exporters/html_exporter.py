import os
import base64
from datetime import datetime
from pathlib import Path
from config import EXPORTS_DIR

def file_to_base64(filepath):
    if not filepath or not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "rb") as f:
            data = f.read()
            encoded = base64.b64encode(data).decode('utf-8')
            ext = Path(filepath).suffix.lower().replace('.', '')
            if ext in ['jpg', 'jpeg']:
                mime = 'image/jpeg'
            elif ext == 'png':
                mime = 'image/png'
            elif ext == 'webp':
                mime = 'image/webp'
            else:
                mime = 'image/jpeg'
            return f"data:{mime};base64,{encoded}"
    except Exception as e:
        print(f"Error encoding image {filepath}: {e}")
        return None

def generate_html_report(visits, title="Xartech Client Visits Report", filter_info="All Visits"):
    """
    Generates a single self-contained, responsive, dashboard-style HTML file
    with Base64 embedded photos, search bar, statistics, and print-ready design.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Xartech_Visits_Report_{timestamp}.html"
    filepath = EXPORTS_DIR / filename
    
    total_visits = len(visits)
    agents_count = len(set(v.get('agent_name', '') for v in visits))
    
    # Process visits to embed base64 images
    processed_visits = []
    for v in visits:
        v_dict = dict(v)
        v_dict['shop_photo_b64'] = file_to_base64(v_dict.get('shop_photo_path'))
        v_dict['card_photo_b64'] = file_to_base64(v_dict.get('card_photo_path'))
        processed_visits.append(v_dict)

    # Build HTML Content
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-gradient: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
            --card-bg: rgba(30, 41, 59, 0.7);
            --card-border: rgba(255, 255, 255, 0.1);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #6366f1;
            --accent-secondary: #06b6d4;
            --accent-green: #10b981;
            --accent-glow: rgba(99, 102, 241, 0.25);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-gradient);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 30px 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        /* Header */
        .header {{
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 24px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 28px;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .brand-logo {{
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 24px;
            color: #ffffff;
            box-shadow: 0 4px 15px var(--accent-glow);
        }}

        .brand-text h1 {{
            font-size: 22px;
            font-weight: 700;
            letter-spacing: -0.5px;
        }}

        .brand-text p {{
            font-size: 13px;
            color: var(--text-secondary);
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}

        .stat-card {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}

        .stat-label {{
            font-size: 13px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .stat-val {{
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(90deg, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        /* Search & Filter Toolbar */
        .toolbar {{
            background: var(--card-bg);
            backdrop-filter: blur(12px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 16px 20px;
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            align-items: center;
            margin-bottom: 28px;
        }}

        .search-box {{
            flex: 1;
            min-width: 250px;
            position: relative;
        }}

        .search-input {{
            width: 100%;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 12px 16px;
            color: #fff;
            font-size: 14px;
            font-family: inherit;
            outline: none;
            transition: all 0.2s;
        }}

        .search-input:focus {{
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }}

        .btn-print {{
            background: linear-gradient(135deg, var(--accent-primary), #4f46e5);
            color: #fff;
            border: none;
            padding: 12px 20px;
            border-radius: 10px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .btn-print:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--accent-glow);
        }}

        /* Visits Grid */
        .visits-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
            gap: 24px;
        }}

        .visit-card {{
            background: var(--card-bg);
            backdrop-filter: blur(14px);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            transition: transform 0.25s ease, border-color 0.25s ease;
        }}

        .visit-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(99, 102, 241, 0.4);
        }}

        .card-images {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            height: 180px;
            background: rgba(0,0,0,0.3);
            border-bottom: 1px solid var(--card-border);
        }}

        .image-box {{
            position: relative;
            overflow: hidden;
            height: 100%;
            cursor: pointer;
        }}

        .image-box img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}

        .image-box:hover img {{
            transform: scale(1.08);
        }}

        .image-badge {{
            position: absolute;
            bottom: 8px;
            left: 8px;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(8px);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            color: #e2e8f0;
        }}

        .no-image {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: var(--text-secondary);
            font-size: 12px;
            text-align: center;
            background: rgba(15, 23, 42, 0.4);
        }}

        .card-body {{
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            flex: 1;
        }}

        .card-title-row {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }}

        .shop-name {{
            font-size: 18px;
            font-weight: 700;
            color: #ffffff;
            line-height: 1.3;
        }}

        .badge-id {{
            background: rgba(99, 102, 241, 0.15);
            color: #818cf8;
            border: 1px solid rgba(99, 102, 241, 0.3);
            padding: 2px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
        }}

        .info-row {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13.5px;
            color: #cbd5e1;
        }}

        .info-row svg {{
            width: 16px;
            height: 16px;
            color: var(--accent-secondary);
            flex-shrink: 0;
        }}

        .info-row strong {{
            color: var(--text-secondary);
            font-weight: 500;
            min-width: 65px;
        }}

        .remarks-box {{
            background: rgba(15, 23, 42, 0.5);
            border-left: 3px solid var(--accent-primary);
            padding: 8px 12px;
            border-radius: 0 8px 8px 0;
            font-size: 12.5px;
            color: #94a3b8;
            font-style: italic;
            margin-top: 4px;
        }}

        .card-footer {{
            margin-top: auto;
            padding-top: 14px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 12px;
            color: var(--text-secondary);
        }}

        .agent-pill {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent-green);
            padding: 3px 10px;
            border-radius: 20px;
            font-weight: 600;
        }}

        /* Modal for full photo preview */
        .modal {{
            display: none;
            position: fixed;
            z-index: 9999;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(10px);
            align-items: center;
            justify-content: center;
        }}

        .modal.active {{
            display: flex;
        }}

        .modal img {{
            max-width: 90vw;
            max-height: 85vh;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.8);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        .modal-close {{
            position: absolute;
            top: 24px;
            right: 28px;
            font-size: 32px;
            color: #fff;
            cursor: pointer;
        }}

        @media print {{
            body {{
                background: #fff !important;
                color: #000 !important;
                padding: 0;
            }}
            .toolbar, .btn-print, .brand-logo {{
                display: none !important;
            }}
            .header, .stat-card, .visit-card {{
                background: #fff !important;
                border: 1px solid #ddd !important;
                color: #000 !important;
                box-shadow: none !important;
                break-inside: avoid;
            }}
            .shop-name, .stat-val {{
                color: #000 !important;
                -webkit-text-fill-color: #000 !important;
            }}
            .info-row, .info-row strong, .card-footer {{
                color: #333 !important;
            }}
            .visits-grid {{
                grid-template-columns: repeat(2, 1fr) !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <div class="brand">
                <div class="brand-logo">X</div>
                <div class="brand-text">
                    <h1>XARTECH CLIENT VISITS REPORT</h1>
                    <p>Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')} &bull; Filter: {filter_info}</p>
                </div>
            </div>
            <div>
                <button class="btn-print" onclick="window.print()">
                    🖨️ Print / Save as PDF
                </button>
            </div>
        </header>

        <!-- Stats -->
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-label">Total Client Visits</span>
                <span class="stat-val">{total_visits}</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Active Field Interns/Agents</span>
                <span class="stat-val">{agents_count}</span>
            </div>
            <div class="stat-card">
                <span class="stat-label">Report Status</span>
                <span class="stat-val" style="color: var(--accent-green);">Verified</span>
            </div>
        </div>

        <!-- Search Bar -->
        <div class="toolbar">
            <div class="search-box">
                <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search by Shop Name, Agent, Phone, or Address..." onkeyup="filterCards()">
            </div>
        </div>

        <!-- Visits Cards Grid -->
        <div class="visits-grid" id="visitsGrid">
"""

    if not processed_visits:
        html_content += """
            <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-secondary);">
                <h2>No visits recorded yet.</h2>
                <p>Visits logged via Telegram Bot will appear here.</p>
            </div>
        """
    else:
        for v in processed_visits:
            shop_img_html = f'<div class="image-box" onclick="openModal(\'{v["shop_photo_b64"]}\')"><img src="{v["shop_photo_b64"]}" alt="Shop Photo" loading="lazy"><span class="image-badge">📸 Shop Photo</span></div>' if v.get('shop_photo_b64') else '<div class="no-image">No Shop Photo</div>'
            
            card_img_html = f'<div class="image-box" onclick="openModal(\'{v["card_photo_b64"]}\')"><img src="{v["card_photo_b64"]}" alt="Visiting Card" loading="lazy"><span class="image-badge">🪪 Visiting Card</span></div>' if v.get('card_photo_b64') else '<div class="no-image">No Visiting Card</div>'
            
            maps_link = ""
            if v.get('latitude') and v.get('longitude'):
                maps_link = f'<a href="https://www.google.com/maps?q={v["latitude"]},{v["longitude"]}" target="_blank" style="color: var(--accent-secondary); text-decoration: underline; margin-left: 6px;">(Open Maps)</a>'
                
            formatted_date = v.get('created_at', '')
            try:
                dt = datetime.fromisoformat(formatted_date)
                formatted_date = dt.strftime('%d %b %Y, %I:%M %p')
            except Exception:
                pass

            html_content += f"""
            <div class="visit-card" data-search="{v.get('shop_name', '').lower()} {v.get('agent_name', '').lower()} {v.get('phone_number', '').lower()} {v.get('address', '').lower() or ''}">
                <div class="card-images">
                    {shop_img_html}
                    {card_img_html}
                </div>
                <div class="card-body">
                    <div class="card-title-row">
                        <h2 class="shop-name">{v.get('shop_name', 'N/A')}</h2>
                        <span class="badge-id">#{v.get('id', '0')}</span>
                    </div>

                    <div class="info-row">
                        <strong>Owner:</strong>
                        <span>{v.get('owner_name') or 'Not specified'}</span>
                    </div>

                    <div class="info-row">
                        <strong>Phone:</strong>
                        <span><a href="tel:{v.get('phone_number')}" style="color: #fff; text-decoration: none;">📞 {v.get('phone_number', 'N/A')}</a></span>
                    </div>

                    <div class="info-row">
                        <strong>Address:</strong>
                        <span>📍 {v.get('address') or 'GPS Location Recorded'}{maps_link}</span>
                    </div>

                    {f'<div class="remarks-box">📝 "{v.get("remarks")}"</div>' if v.get('remarks') else ''}

                    <div class="card-footer">
                        <span class="agent-pill">👤 {v.get('agent_name', 'Agent')}</span>
                        <span>🕒 {formatted_date}</span>
                    </div>
                </div>
            </div>
            """

    html_content += """
        </div>
    </div>

    <!-- Modal -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="modal-close">&times;</span>
        <img id="modalImg" src="" alt="Full View">
    </div>

    <script>
        function filterCards() {
            const query = document.getElementById('searchInput').value.toLowerCase();
            const cards = document.querySelectorAll('.visit-card');
            cards.forEach(card => {
                const searchData = card.getAttribute('data-search') || '';
                if (searchData.includes(query)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        }

        function openModal(src) {
            if(!src) return;
            document.getElementById('modalImg').src = src;
            document.getElementById('imageModal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('imageModal').classList.remove('active');
        }
    </script>
</body>
</html>
"""

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filepath
