# Dossier PDF - Zone de Test

Ce dossier est organisé pour faciliter vos tests avec OptimOCR2.

## 📁 Structure

```
pdf/
├── to_process/     ← Placez vos PDFs ICI pour les traiter
├── processed/      ← PDFs déjà traités (archivage)
└── samples/        ← Exemples de PDFs pour tests
```

## 🚀 Utilisation Rapide

### 1. Placer vos PDFs

```bash
# Copiez vos PDFs dans to_process/
cp mon_document.pdf pdf/to_process/
```

### 2. Traiter un PDF

```bash
# Test rapide (première page seulement)
python test_document.py pdf/to_process/mon_document.pdf

# Traitement complet
python main.py pdf/to_process/mon_document.pdf --quality balanced -vv
```

### 3. Traitement en Batch

```bash
# Traiter tous les PDFs du dossier
python process_batch.py

# Ou manuellement
for pdf in pdf/to_process/*.pdf; do
    python main.py "$pdf" --quality balanced -vv
done
```

## 📊 Résultats

Les fichiers DOCX générés seront dans le dossier `output/`

```
output/
├── mon_document.docx
├── autre_doc.docx
└── ...
```

## 🎯 Modes de Qualité

### Mode Fast (Rapide)
```bash
python main.py pdf/to_process/doc.pdf --quality fast
```
- Temps : ~2s/page
- Précision : 92-94%
- Usage : Documents propres, tests rapides

### Mode Balanced (Équilibré) - **RECOMMANDÉ**
```bash
python main.py pdf/to_process/doc.pdf --quality balanced
```
- Temps : ~3-5s/page
- Précision : 96-98%
- Usage : Usage général

### Mode Quality (Qualité)
```bash
python main.py pdf/to_process/doc.pdf --quality quality
```
- Temps : ~10-15s/page
- Précision : 98-99.5%
- Usage : Documents importants
- Nécessite : `pip install easyocr`

### Mode Ultra (Maximum)
```bash
python main.py pdf/to_process/doc.pdf --quality ultra
```
- Temps : ~25-35s/page
- Précision : 99-99.8%
- Usage : Précision critique
- Nécessite : `pip install easyocr`

## 🧪 Exemples de Test

### Test sur Pages Spécifiques

```bash
# Pages 1 à 10
python main.py pdf/to_process/livre.pdf --pages 1-10

# Pages spécifiques
python main.py pdf/to_process/doc.pdf --pages "1,5,10-15,20"
```

### Test avec Différents Langages

```bash
# Anglais
python main.py pdf/to_process/english_doc.pdf --language eng

# Français (par défaut)
python main.py pdf/to_process/french_doc.pdf --language fra
```

## 📋 Checklist Avant Traitement

Avant de traiter un gros lot de PDFs :

- [ ] Tester sur la première page : `python test_document.py pdf/to_process/doc.pdf`
- [ ] Vérifier la qualité du résultat dans `output/`
- [ ] Ajuster le mode de qualité si nécessaire
- [ ] Vérifier l'espace disque disponible
- [ ] Estimer le temps total : (nombre de pages × temps par page)

## 🔍 Analyser la Qualité d'un PDF

```bash
# Obtenir des infos sur le PDF
python main.py info pdf/to_process/mon_doc.pdf
```

Cela affichera :
- Nombre de pages
- Taille du fichier
- Temps estimé de traitement

## 📦 Archivage

Une fois traités, déplacez les PDFs :

```bash
# Déplacer vers processed/
mv pdf/to_process/mon_document.pdf pdf/processed/
```

## ⚠️ Notes Importantes

1. **Les PDFs ne sont PAS versionnés** (exclus par .gitignore)
2. **Taille maximale recommandée** : 100 MB par PDF
3. **Format supporté** : PDF scannés (images), pas de PDF texte natif
4. **Langues disponibles** : Voir `python main.py languages`

## 💡 Astuces

### Pour Documents Anciens/Délavés
```python
# Éditer config.py
USE_ADVANCED_BINARIZATION = True
BINARIZATION_METHOD = 'sauvola'
USE_SHADOW_REMOVAL = True
```

### Pour Documents Photographiés
```python
# Éditer config.py
USE_PERSPECTIVE_CORRECTION = True
USE_SHADOW_REMOVAL = True
```

### Pour Documents Multilingues
```bash
python main.py pdf/to_process/doc.pdf --language fra+eng
```

## 📞 Besoin d'Aide ?

- Voir [TESTING_GUIDE.md](../TESTING_GUIDE.md) pour le guide complet
- Voir [ENHANCEMENTS.md](../ENHANCEMENTS.md) pour les fonctionnalités avancées
- Issues GitHub : [OptimOCR2 Issues](https://github.com/iguane39/OptimOCR2/issues)

---

**Prêt à commencer ?** Placez vos PDFs dans `to_process/` et lancez vos tests ! 🚀
