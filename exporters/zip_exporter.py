import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from config import EXPORTS_DIR
from exporters.excel_exporter import generate_excel_report
from exporters.html_exporter import generate_html_report

def generate_zip_package(visits, title="Xartech_Visits_Archive"):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"Xartech_Complete_Data_{timestamp}.zip"
    zip_filepath = EXPORTS_DIR / zip_filename
    
    # Create temporary staging folder
    staging_dir = EXPORTS_DIR / f"staging_{timestamp}"
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Generate Excel & HTML into staging
        excel_path = generate_excel_report(visits)
        html_path = generate_html_report(visits)
        
        shutil.copy(excel_path, staging_dir / excel_path.name)
        shutil.copy(html_path, staging_dir / html_path.name)
        
        # 2. Create organized photos directory
        photos_folder = staging_dir / "Photos_Organized"
        photos_folder.mkdir(parents=True, exist_ok=True)
        
        for v in visits:
            visit_id = v.get('id', '0')
            safe_shop_name = "".join(c for c in v.get('shop_name', 'Shop') if c.isalnum() or c in (' ', '_', '-')).strip()
            folder_name = f"Visit_{visit_id}_{safe_shop_name}"
            shop_dir = photos_folder / folder_name
            shop_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy shop photo
            if v.get('shop_photo_path') and os.path.exists(v['shop_photo_path']):
                ext = Path(v['shop_photo_path']).suffix or '.jpg'
                shutil.copy(v['shop_photo_path'], shop_dir / f"Shop_Front{ext}")
                
            # Copy card photo
            if v.get('card_photo_path') and os.path.exists(v['card_photo_path']):
                ext = Path(v['card_photo_path']).suffix or '.jpg'
                shutil.copy(v['card_photo_path'], shop_dir / f"Visiting_Card{ext}")
                
        # 3. Zip everything up
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(staging_dir):
                for file in files:
                    full_path = Path(root) / file
                    arcname = full_path.relative_to(staging_dir)
                    zipf.write(full_path, arcname)
                    
        return zip_filepath
    finally:
        # Clean up staging directory
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)
