#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module extraction images HTML amélioré
Extrait: attachments + base64 inline + CID + CSS background
"""

import re
import base64
import os
from pathlib import Path
from email import message_from_file
from datetime import datetime

def extraire_images_attachees(msg, email_id, output_dir):
    """Extrait les images attachées (original)"""
    images = []
    
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_maintype() == 'image':
                try:
                    filename = part.get_filename()
                    if not filename:
                        ext = part.get_content_subtype()
                        filename = f"{email_id}_attachment_{len(images)}.{ext}"
                    
                    filepath = Path(output_dir) / filename
                    image_data = part.get_payload(decode=True)
                    
                    with open(filepath, 'wb') as f:
                        f.write(image_data)
                    
                    images.append(str(filepath))
                except Exception as e:
                    pass
    
    return images


def extraire_images_html_base64(contenu_html, email_id, output_dir):
    """
    Extrait les images inline base64 des emails HTML
    Patterns:
      - <img src="data:image/png;base64,...">
      - <img src="data:image/jpeg;base64,...">
    """
    pattern = r'data:image/([^;]+);base64,([A-Za-z0-9+/=]+)'
    matches = re.findall(pattern, contenu_html, re.IGNORECASE)
    
    images = []
    
    for idx, (format_img, data_base64) in enumerate(matches):
        try:
            # Décoder base64
            image_data = base64.b64decode(data_base64)
            
            # Valider que c'est vraiment une image (header PNG/JPEG)
            if not (image_data[:4] == b'\x89PNG' or image_data[:2] == b'\xff\xd8'):
                continue
            
            # Sauver
            filename = f"{email_id}_html_base64_{idx}.{format_img.lower()}"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            images.append(str(filepath))
        
        except Exception as e:
            pass
    
    return images


def extraire_images_html_cid(msg, email_id, output_dir):
    """
    Extrait les images référencées par CID (Content-ID)
    Patterns:
      - <img src="cid:image@01D6E4F5.2A1C0AC0">
      - Background-image: url(cid:...)
    """
    images = []
    
    if msg.is_multipart():
        cid_parts = {}
        
        # Chercher tous les parts avec Content-ID
        for part in msg.walk():
            content_id = part.get('Content-ID')
            
            if content_id and part.get_content_maintype() == 'image':
                cid_clean = content_id.strip('<>')
                cid_parts[cid_clean] = part
        
        # Sauver les images
        for cid, part in cid_parts.items():
            try:
                image_data = part.get_payload(decode=True)
                content_type = part.get_content_type()
                format_img = content_type.split('/')[-1]
                
                filename = f"{email_id}_cid_{cid[:20]}.{format_img}"
                filepath = Path(output_dir) / filename
                
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                images.append(str(filepath))
            
            except Exception as e:
                pass
    
    return images


def extraire_images_css_url(contenu_html, email_id, output_dir):
    """
    Extrait les images CSS background
    Patterns:
      - background-image: url('data:image/png;base64,...')
      - background: url("data:image/jpeg;base64,...")
    """
    pattern = r"url\(['\"]?data:image/([^;]+);base64,([A-Za-z0-9+/=]+)['\"]?\)"
    matches = re.findall(pattern, contenu_html, re.IGNORECASE)
    
    images = []
    
    for idx, (format_img, data_base64) in enumerate(matches):
        try:
            image_data = base64.b64decode(data_base64)
            
            # Valider image
            if not (image_data[:4] == b'\x89PNG' or image_data[:2] == b'\xff\xd8'):
                continue
            
            filename = f"{email_id}_css_bg_{idx}.{format_img.lower()}"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            images.append(str(filepath))
        
        except Exception as e:
            pass
    
    return images


def extraire_images_email_v2(chemin_eml, email_id, output_dir):
    """
    EXTRACTION COMPLÈTE v2.0
    Combine: attachments + HTML base64 + CID + CSS background
    """
    images_totales = []
    
    try:
        with open(chemin_eml, 'r', encoding='utf-8', errors='ignore') as f:
            msg = message_from_file(f)
    
    except Exception as e:
        return images_totales
    
    # 1. Images attachées (original)
    images_totales.extend(extraire_images_attachees(msg, email_id, output_dir))
    
    # 2. Images HTML
    for part in msg.walk():
        if part.get_content_type() in ['text/html', 'text/plain']:
            try:
                if part.get_content_type() == 'text/html':
                    html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    # Extraire base64
                    images_totales.extend(
                        extraire_images_html_base64(html, email_id, output_dir)
                    )
                    
                    # Extraire CSS backgrounds
                    images_totales.extend(
                        extraire_images_css_url(html, email_id, output_dir)
                    )
            
            except Exception as e:
                pass
    
    # 3. Images CID
    images_totales.extend(extraire_images_html_cid(msg, email_id, output_dir))
    
    return images_totales


def generer_extraction_v2():
    """Exécute extraction complète v2.0 sur tous les emails"""
    
    emails_dir = Path('emails_extraits')
    images_dir = Path('images_extraites')
    
    if not emails_dir.exists():
        print(f"❌ Dossier {emails_dir} non trouvé")
        return False
    
    if not images_dir.exists():
        images_dir.mkdir()
    
    eml_files = sorted(emails_dir.glob('email_*.eml'))
    print(f"📧 Extraction v2.0 pour {len(eml_files)} emails...\n")
    
    stats = {
        'total_emails': len(eml_files),
        'emails_avec_images': 0,
        'total_images': 0,
        'attachments': 0,
        'html_base64': 0,
        'cid': 0,
        'css_backgrounds': 0,
    }
    
    for idx, chemin_eml in enumerate(eml_files, 1):
        email_id = chemin_eml.stem
        
        images = extraire_images_email_v2(str(chemin_eml), email_id, str(images_dir))
        
        if images:
            stats['emails_avec_images'] += 1
            stats['total_images'] += len(images)
            
            # Catégoriser
            for img in images:
                if 'attachment' in img:
                    stats['attachments'] += 1
                elif 'base64' in img:
                    stats['html_base64'] += 1
                elif 'cid' in img:
                    stats['cid'] += 1
                elif 'css' in img:
                    stats['css_backgrounds'] += 1
        
        # Progress
        if idx % 50 == 0 or idx == len(eml_files):
            print(f"  ✓ {idx}/{len(eml_files)} emails traités... ({stats['total_images']} images trouvées)")
    
    print(f"\n{'='*70}")
    print(f"✅ EXTRACTION V2.0 COMPLÉTÉE")
    print(f"{'='*70}")
    print(f"  Total images: {stats['total_images']}")
    print(f"  Emails avec images: {stats['emails_avec_images']}/481 ({100*stats['emails_avec_images']/481:.1f}%)")
    print(f"  Attachments: {stats['attachments']}")
    print(f"  HTML Base64: {stats['html_base64']}")
    print(f"  CID: {stats['cid']}")
    print(f"  CSS Backgrounds: {stats['css_backgrounds']}")
    print(f"{'='*70}\n")
    
    # Sauver stats
    with open('stats_extraction_v2.json', 'w') as f:
        import json
        json.dump(stats, f, indent=2)
    
    return True


if __name__ == '__main__':
    generer_extraction_v2()
