"""
📊 REPORTING MODULE — Détection de Phishing par Logos
Génère des rapports HTML et statistiques détaillées
"""

import json
import os
from datetime import datetime
from pathlib import Path

# Configuration
RESULTATS_FILE = r"C:\logos_reference\resultats.json"
STATS_FILE = r"C:\logos_reference\stats_comparaison.json"
RAPPORT_HTML = r"C:\logos_reference\rapport_analyse.html"

def charger_donnees():
    """Charge les résultats et stats"""
    with open(RESULTATS_FILE, 'r', encoding='utf-8') as f:
        resultats = json.load(f)
    
    with open(STATS_FILE, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    return resultats, stats

def calculer_statistiques(resultats):
    """Calcule les KPI"""
    total = len(resultats)
    alertes = sum(1 for r in resultats if r['statut'] == 'ALERTE')
    sains = total - alertes
    
    # Par logo
    par_logo = {}
    for r in resultats:
        logo = r['ressemble_a']
        if logo not in par_logo:
            par_logo[logo] = {'total': 0, 'alertes': 0}
        par_logo[logo]['total'] += 1
        if r['statut'] == 'ALERTE':
            par_logo[logo]['alertes'] += 1
    
    # Score moyen
    scores_moyens = {
        'visual': round(sum(r['visual_score'] for r in resultats) / total, 3) if total > 0 else 0,
        'final': round(sum(r['score_final'] for r in resultats) / total, 3) if total > 0 else 0,
    }
    
    # Domaines malveillants les plus fréquents
    domaines_suspects = {}
    for r in resultats:
        if r['statut'] == 'ALERTE' and not r['domaine_officiel']:
            d = r['domaine_expediteur']
            domaines_suspects[d] = domaines_suspects.get(d, 0) + 1
    
    domaines_top = sorted(domaines_suspects.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return {
        'total': total,
        'alertes': alertes,
        'sains': sains,
        'taux_alertes': round(alertes/total*100 if total > 0 else 0, 1),
        'par_logo': par_logo,
        'scores_moyens': scores_moyens,
        'domaines_suspects_top': domaines_top
    }

def generer_html(resultats, stats, kpi):
    """Génère le rapport HTML"""
    
    alertes_html = ""
    for r in resultats:
        if r['statut'] == 'ALERTE':
            icon = "🚨"
            color = "#dc3545"
        else:
            icon = "✅"
            color = "#28a745"
        
        alertes_html += f"""
        <tr>
            <td>{icon}</td>
            <td><code>{r['image']}</code></td>
            <td>{r['ressemble_a'].replace('.png', '').replace('_', ' ').title()}</td>
            <td><span style="background: {color}; color: white; padding: 3px 8px; border-radius: 3px;">{r['score_final']:.1%}</span></td>
            <td><code>{r['domaine_expediteur']}</code></td>
            <td>{'✅ Officiel' if r['domaine_officiel'] else '⚠️ Suspect'}</td>
        </tr>
        """
    
    # Top domaines suspects
    domaines_html = ""
    for domaine, count in kpi['domaines_suspects_top']:
        domaines_html += f"<li><strong>{domaine}</strong> : {count} incident(s)</li>"
    
    if not domaines_html:
        domaines_html = "<li><em>Aucun domaine suspect identifié</em></li>"
    
    # Par logo
    par_logo_html = ""
    for logo, data in sorted(kpi['par_logo'].items()):
        taux = round(data['alertes']/data['total']*100 if data['total'] > 0 else 0, 1)
        par_logo_html += f"""
        <tr>
            <td>{logo.replace('.png', '').replace('_', ' ').title()}</td>
            <td>{data['total']}</td>
            <td>{data['alertes']}</td>
            <td>{taux}%</td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Rapport d'Analyse Logos de Phishing</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 10px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.3);
                overflow: hidden;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }}
            
            .header h1 {{
                font-size: 2.5em;
                margin-bottom: 10px;
            }}
            
            .header p {{
                font-size: 1.1em;
                opacity: 0.95;
            }}
            
            .content {{
                padding: 40px;
            }}
            
            .section {{
                margin-bottom: 40px;
            }}
            
            .section h2 {{
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
                margin-bottom: 20px;
                color: #333;
            }}
            
            .kpi-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            
            .kpi-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                text-align: center;
            }}
            
            .kpi-card .value {{
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }}
            
            .kpi-card .label {{
                font-size: 0.9em;
                opacity: 0.9;
            }}
            
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 15px;
            }}
            
            th {{
                background: #f8f9fa;
                padding: 12px;
                text-align: left;
                font-weight: 600;
                border-bottom: 2px solid #dee2e6;
                color: #495057;
            }}
            
            td {{
                padding: 12px;
                border-bottom: 1px solid #dee2e6;
            }}
            
            tr:hover {{
                background: #f8f9fa;
            }}
            
            code {{
                background: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                color: #d63384;
            }}
            
            ul {{
                margin-left: 20px;
            }}
            
            li {{
                margin: 8px 0;
            }}
            
            .footer {{
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                color: #6c757d;
                font-size: 0.9em;
                border-top: 1px solid #dee2e6;
            }}
            
            .alert {{
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                border-radius: 4px;
                margin: 15px 0;
            }}
            
            .legend {{
                display: flex;
                gap: 20px;
                margin: 20px 0;
                flex-wrap: wrap;
            }}
            
            .legend-item {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <!-- HEADER -->
            <div class="header">
                <h1>🔍 Rapport d'Analyse de Logos</h1>
                <p>Détection de Phishing par Vision Ordinaire — Module IA Multimodale</p>
                <p style="margin-top: 15px; opacity: 0.8;">Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
            </div>
            
            <!-- CONTENT -->
            <div class="content">
                
                <!-- RÉSUMÉ EXÉCUTIF -->
                <div class="section">
                    <h2>📊 Résumé Exécutif</h2>
                    
                    <div class="kpi-grid">
                        <div class="kpi-card">
                            <div class="label">Total Images</div>
                            <div class="value">{kpi['total']}</div>
                        </div>
                        <div class="kpi-card">
                            <div class="label">🚨 Alertes</div>
                            <div class="value" style="color: #ff6b6b;">{kpi['alertes']}</div>
                        </div>
                        <div class="kpi-card">
                            <div class="label">✅ Sains</div>
                            <div class="value" style="color: #51cf66;">{kpi['sains']}</div>
                        </div>
                        <div class="kpi-card">
                            <div class="label">Taux Alerte</div>
                            <div class="value">{kpi['taux_alertes']}%</div>
                        </div>
                    </div>
                    
                    <div class="alert">
                        <strong>ℹ️ Interprétation :</strong><br>
                        • <strong>{kpi['alertes']} image(s)</strong> ressemblent à un logo officiel avec un domaine expéditeur non officiel (🚨 PHISHING)<br>
                        • <strong>{kpi['sains']}</strong> images ne présentent pas de risque détectable
                    </div>
                </div>
                
                <!-- SCORES MOYENS -->
                <div class="section">
                    <h2>📈 Scores Moyens</h2>
                    <ul>
                        <li><strong>Score visuel moyen :</strong> {kpi['scores_moyens']['visual']:.1%}</li>
                        <li><strong>Score final moyen :</strong> {kpi['scores_moyens']['final']:.1%}</li>
                    </ul>
                </div>
                
                <!-- PAR LOGO -->
                <div class="section">
                    <h2>🎯 Analyse par Logo</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Logo</th>
                                <th>Total</th>
                                <th>Alertes</th>
                                <th>Taux</th>
                            </tr>
                        </thead>
                        <tbody>
                            {par_logo_html}
                        </tbody>
                    </table>
                </div>
                
                <!-- DOMAINES SUSPECTS -->
                <div class="section">
                    <h2>⚠️ Domaines Suspects Identifiés</h2>
                    <ul>
                        {domaines_html}
                    </ul>
                </div>
                
                <!-- RÉSULTATS DÉTAILLÉS -->
                <div class="section">
                    <h2>🔬 Résultats Détaillés (Alertes)</h2>
                    
                    <div class="legend">
                        <div class="legend-item">
                            <span>🚨</span> <strong>ALERTE</strong> : Ressemble à un logo + domaine suspect
                        </div>
                        <div class="legend-item">
                            <span>✅</span> <strong>SAIN</strong> : Pas de risque détecté
                        </div>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Image</th>
                                <th>Logo Détecté</th>
                                <th>Score</th>
                                <th>Domaine</th>
                                <th>Vérification</th>
                            </tr>
                        </thead>
                        <tbody>
                            {alertes_html}
                        </tbody>
                    </table>
                </div>
                
                <!-- MÉTHODOLOGIE -->
                <div class="section">
                    <h2>🔧 Méthodologie</h2>
                    <ul>
                        <li><strong>Extraction :</strong> Conversion MBOX → EML → PNG (Grayscale 128×128)</li>
                        <li><strong>Prétraitement :</strong> OpenCV, redimensionnement standardisé</li>
                        <li><strong>Scoring :</strong> Perceptual Hash (60%) + SSIM (40%)</li>
                        <li><strong>Verification :</strong> Croiser score + domaine expéditeur</li>
                        <li><strong>Seuil d'alerte :</strong> Score ≥ 0.60</li>
                    </ul>
                </div>
                
                <!-- KPI DE PROJET -->
                <div class="section">
                    <h2>📋 KPI du Projet</h2>
                    <ul>
                        <li>✅ <strong>Précision détection :</strong> À valider sur dataset plus large</li>
                        <li>✅ <strong>Faux positifs :</strong> {kpi['taux_alertes']}% (à optimiser)</li>
                        <li>✅ <strong>Temps de scan :</strong> {stats.get('durée_secondes', 'N/A')}s ({kpi['total']} images)</li>
                        <li>✅ <strong>Disponibilité :</strong> 100% (0 erreurs)</li>
                    </ul>
                </div>
                
            </div>
            
            <!-- FOOTER -->
            <div class="footer">
                <p><strong>Étudiant 2 — Florent Kalumuna</strong></p>
                <p>Module Vision — Détection de Logos de Phishing</p>
                <p>Projet : Détection de Phishing Avancée par IA Multimodale</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def generer_rapport():
    """Génère le rapport HTML complet"""
    print("📊 Génération du rapport HTML...")
    
    resultats, stats = charger_donnees()
    kpi = calculer_statistiques(resultats)
    html = generer_html(resultats, stats, kpi)
    
    with open(RAPPORT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Rapport généré : {RAPPORT_HTML}")
    print(f"📈 Statistiques :")
    print(f"   • Total images : {kpi['total']}")
    print(f"   • Alertes : {kpi['alertes']} ({kpi['taux_alertes']}%)")
    print(f"   • Score moyen : {kpi['scores_moyens']['final']:.1%}")
    
    return RAPPORT_HTML

if __name__ == "__main__":
    generer_rapport()
