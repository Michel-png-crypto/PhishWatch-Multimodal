#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Génère metrics formelles: Precision, Recall, F1
Compare resultats_fusion contre ground truth (PhishTank + labels manuels)
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

EMAIL_ID_VALID_RE = re.compile(r"^email_\d{4}$")


def email_id_valide(email_id: str) -> bool:
    return bool(EMAIL_ID_VALID_RE.match(email_id or ""))


def charger_ground_truth() -> dict:
    ground_truth_file = Path("ground_truth.json")
    if not ground_truth_file.exists():
        return {}
    try:
        with open(ground_truth_file, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return {}

    if isinstance(data, dict):
        return {str(k): int(v) for k, v in data.items() if str(v).isdigit()}

    labels = {}
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                continue
            key = item.get("email_id") or item.get("email") or item.get("fichier")
            label = item.get("label") or item.get("truth") or item.get("ground_truth")
            if key and isinstance(label, (int, str)) and str(label).isdigit():
                labels[str(key)] = int(label)
    return labels


def enrichir_ground_truth_phishtank(ground_truth: dict) -> dict:
    """Ajoute les emails dont les URLs matchent PhishTank/OpenPhish."""
    phish_file = Path("phishing_urls.txt")
    emails_dir = Path("emails_extraits")
    if not phish_file.exists() or not emails_dir.exists():
        return ground_truth

    try:
        from generer_resultats_urls import extraire_urls_email
    except ImportError:
        return ground_truth

    phish = {line.strip() for line in phish_file.read_text(encoding="utf-8").splitlines() if line.strip()}
    labels = dict(ground_truth)

    for eml in sorted(emails_dir.glob("email_*.eml")):
        eid = eml.stem
        if labels.get(eid) == 1:
            continue
        for url in extraire_urls_email(str(eml)):
            if any(p in url or url in p for p in phish):
                labels[eid] = 1
                break

    return labels


def predire_phishing(resultat: dict) -> int:
    """Aligné sur statut_fusion (pas seulement le score numérique)."""
    if resultat.get("statut_fusion") == "PHISHING":
        return 1
    return 0


def generer_metrics():
    fusion_file = Path("resultats_fusion.json")

    if not fusion_file.exists():
        print(f"[ERR] Fichier {fusion_file} non trouvé")
        print("   Exécute d'abord: python fusion_multimodale.py")
        return False

    try:
        with open(fusion_file, encoding="utf-8") as f:
            fusion_data = json.load(f)
    except Exception as e:
        print(f"[ERR] Erreur lecture {fusion_file}: {e}")
        return False

    resultats_bruts = fusion_data.get("resultats", [])
    resultats = [r for r in resultats_bruts if email_id_valide(r.get("email_id", ""))]

    if not resultats:
        print("[ERR] Pas de données valides dans resultats_fusion.json")
        return False

    ignores = len(resultats_bruts) - len(resultats)
    if ignores:
        print(f"[INFO] {ignores} entrées orphelines ignorées (images sans email_id valide).")

    ground_truth = enrichir_ground_truth_phishtank(charger_ground_truth())
    if ground_truth:
        print(f"[INFO] Ground truth : {len(ground_truth)} label(s) ({sum(ground_truth.values())} phishing).")
    else:
        print("[WARN] Aucun ground truth — métriques peu fiables.")

    y_pred = [predire_phishing(r) for r in resultats]

    y_true = []
    for r in resultats:
        email_id = r.get("email_id") or ""
        if email_id in ground_truth:
            y_true.append(int(ground_truth[email_id]))
            continue

        # Emails sans label explicite = légitimes (conservateur pour la précision)
        y_true.append(0)

    print(f"[INFO] Prédictions PHISHING : {sum(y_pred)} / {len(resultats)}")

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0
    false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "dataset": f"{len(resultats)} emails valides — fusion results",
        "ground_truth_source": "ground_truth.json + PhishTank/OpenPhish",
        "labeled_phishing": int(sum(ground_truth.values())),
        "confusion_matrix": {
            "true_positives": int(tp),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "total": int(total),
        },
        "scores": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "accuracy": round(accuracy, 3),
            "false_positive_rate": round(false_positive_rate, 3),
        },
        "kpi_cdc": {
            "target_precision": ">= 0.90",
            "actual_precision": round(precision, 3),
            "met_precision": precision >= 0.90,
            "target_false_positives": "< 10%",
            "actual_false_positives_percent": round(false_positive_rate * 100, 1),
            "met_false_positives": false_positive_rate <= 0.10,
        },
        "interpretation": {
            "tp": f"{tp} vrais positifs (emails phishing correctement détectés)",
            "tn": f"{tn} vrais négatifs (emails légitimes correctement acceptés)",
            "fp": f"{fp} faux positifs (emails légitimes faussement rejetés)",
            "fn": f"{fn} faux négatifs (emails phishing non détectés)",
            "note": (
                "La précision globale dépend du nombre d'emails étiquetés phishing. "
                "Avec peu de labels confirmés (PhishTank), un FP pèse lourd sur la précision."
            ),
        },
    }

    output_file = Path("metrics_formels.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("[OK] METRICS FORMELS GÉNÉRÉS")
    print("=" * 60)
    print(f"\n[CONFUSION MATRIX]")
    print(f"   TP: {int(tp)}  TN: {int(tn)}  FP: {int(fp)}  FN: {int(fn)}  Total: {int(total)}")
    print(f"\n[SCORES]")
    print(f"   Precision:  {precision:.3f} ({precision * 100:.1f}%)")
    print(f"   Recall:     {recall:.3f} ({recall * 100:.1f}%)")
    print(f"   F1-Score:   {f1:.3f}")
    print(f"   Accuracy:   {accuracy:.3f} ({accuracy * 100:.1f}%)")
    print(f"\n[SAVED] {output_file}")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        success = generer_metrics()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERR] Erreur fatale: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
