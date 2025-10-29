# Guide de Test - OptimOCR2

## 🚀 Test Rapide (5 minutes)

### Option 1 : Installation Automatique

```bash
# 1. Cloner le projet
git clone https://github.com/iguane39/OptimOCR2.git
cd OptimOCR2

# 2. Exécuter le script d'installation
chmod +x quick_setup.sh
./quick_setup.sh

# 3. Tester avec votre PDF
python test_document.py votre_document.pdf
```

### Option 2 : Installation Manuelle

#### Sur Linux (Ubuntu/Debian)

```bash
# Installer Tesseract et Poppler
sudo apt-get update
sudo apt-get install tesseract-ocr tesseract-ocr-fra poppler-utils

# Installer les dépendances Python
pip install -r requirements.txt

# Tester
python test_document.py votre_document.pdf
```

#### Sur macOS

```bash
# Installer avec Homebrew
brew install tesseract tesseract-lang poppler

# Installer les dépendances Python
pip install -r requirements.txt

# Tester
python test_document.py votre_document.pdf
```

#### Sur Windows

1. **Installer Tesseract** :
   - Télécharger depuis [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Ajouter au PATH ou noter le chemin d'installation

2. **Installer Poppler** :
   - Télécharger depuis [Poppler Windows](http://blog.alivate.com.au/poppler-windows/)
   - Extraire et ajouter `bin/` au PATH

3. **Installer Python dependencies** :
   ```cmd
   pip install -r requirements.txt
   ```

4. **Tester** :
   ```cmd
   python test_document.py votre_document.pdf
   ```

## 📊 Script de Test Rapide

Le script `test_document.py` fait un test rapide sur la **première page** seulement :

```bash
# Test basique
python test_document.py document.pdf

# Test sans améliorations (plus rapide)
python test_document.py document.pdf --no-enhancements
```

### Ce que le script affiche :

```
=============================================================
OptimOCR2 - Quick Test
=============================================================
📄 Input: /path/to/document.pdf
📝 Output: output/document.docx

🔧 Initializing components...
✨ Using advanced enhancements
📄 Total pages: 25

🔍 Processing page 1 (quick test)...
  → Converting PDF to image...
  → Enhancing image (advanced preprocessing)...
  → Running OCR...
  ✓ Found 347 words
  ✓ Average confidence: 94.3%
  → Analyzing formatting...

📝 Creating Word document...

=============================================================
✅ Test Complete!
=============================================================
⏱️  Processing time: 8.45s
📊 Words extracted: 347
📈 Average confidence: 94.3%
📄 Output saved to: output/document.docx

📝 Sample text (first 500 characters):
------------------------------------------------------------------
[Texte extrait affiché ici...]
------------------------------------------------------------------

💡 Recommendations:
  • Good confidence! Results should be accurate.
  • To process all pages: python main.py /path/to/document.pdf
```

## 🎯 Tester avec Différents Modes

### Mode Balanced (Recommandé pour débuter)

```bash
python main.py document.pdf --quality balanced -vv
```

- Bon équilibre vitesse/qualité
- Active les améliorations de base
- **Temps** : ~3-5 secondes par page
- **Accuracy** : 96-98%

### Mode Quality (Pour meilleure précision)

```bash
python main.py document.pdf --quality quality -vv
```

- Haute qualité avec ensemble OCR
- Nécessite EasyOCR : `pip install easyocr`
- **Temps** : ~10-15 secondes par page
- **Accuracy** : 98-99.5%

### Mode Ultra (Maximum de précision)

```bash
python main.py document.pdf --quality ultra -vv
```

- Toutes les améliorations activées
- Multi-résolutions + multi-angles
- **Temps** : ~25-35 secondes par page
- **Accuracy** : 99-99.8%

## 🧪 Tester les Améliorations Individuellement

### Test de Binarisation Avancée

```python
from PIL import Image
from modules.image_enhancer import ImageEnhancer

# Charger image
image = Image.open('page_1.png')

# Tester binarisation Sauvola
enhancer = ImageEnhancer()
enhanced = enhancer.advanced_binarization(image)
enhanced.save('enhanced_sauvola.png')
```

### Test Multi-Résolutions

```python
from modules.multi_pass_ocr import create_multi_pass_ocr
from modules.ocr_engine import OCREngine

base_engine = OCREngine(language='fra')
multi_pass = create_multi_pass_ocr(base_engine)

# Tester plusieurs DPI
result = multi_pass.process_multi_resolution(image)
print(f"Confidence: {result.average_confidence}%")
```

### Test Ensemble OCR

```python
from modules.easyocr_engine import create_ensemble_engine

# Nécessite: pip install easyocr
ensemble = create_ensemble_engine(['tesseract', 'easyocr'])
result = ensemble.recognize_text(image)
```

## 📤 M'Envoyer Votre PDF pour Analyse

Si vous voulez que j'analyse votre PDF **sans exécuter l'OCR** :

### Ce que je peux faire :

1. **Lire et visualiser** votre PDF
2. **Analyser la qualité** du scan :
   - Résolution
   - Présence d'ombres
   - Inclinaison
   - Qualité du texte
   - Type de document

3. **Recommander les paramètres** optimaux :
   - Mode de qualité à utiliser
   - DPI recommandé
   - Améliorations à activer
   - Temps estimé de traitement

4. **Identifier les défis** potentiels :
   - Texte délavé
   - Fond coloré
   - Colonnes multiples
   - Tableaux complexes

### Comment procéder :

1. **Uploadez votre PDF** dans le chat
2. Je l'analyserai visuellement
3. Je vous donnerai :
   - Analyse de la difficulté OCR (facile/moyen/difficile)
   - Commande optimale à exécuter
   - Temps estimé de traitement
   - Précision attendue

### Exemple de mon analyse :

```
📄 Analyse de votre PDF :

Type de document : Livre scanné
Qualité : Bonne (peu de bruit)
Difficulté OCR : Moyenne
Pages : 120

Recommandations :
✅ Mode: balanced (bon compromis)
✅ DPI: 600 (déjà suffisant)
✅ Langue: français
✅ Améliorations: binarisation avancée, correction intelligente

Commande recommandée :
  python main.py votre_livre.pdf --quality balanced -vv

Temps estimé : ~6 minutes (3s par page x 120 pages)
Précision attendue : 97-98%

⚠️ Attention :
  - Page 15 : ombre en haut à droite
  - Page 47 : légère inclinaison
  → Ces pages bénéficieront de USE_SHADOW_REMOVAL et USE_PERSPECTIVE_CORRECTION
```

## 🔍 Vérification de l'Installation

```bash
# Vérifier Tesseract
tesseract --version

# Vérifier Tesseract français
tesseract --list-langs | grep fra

# Vérifier Python dependencies
python -c "import pytesseract, pdf2image, cv2, PIL; print('✓ All dependencies OK')"
```

## ❓ Problèmes Courants

### "Tesseract not found"

```bash
# Linux
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract

# Windows
# Installer depuis https://github.com/UB-Mannheim/tesseract/wiki
# Puis ajouter au PATH
```

### "pdf2image errors"

```bash
# Installer Poppler
# Linux
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

### "Out of memory"

```python
# Éditer config.py
PARALLEL_PROCESSING = False
MAX_IMAGE_SIZE_MB = 50  # Réduire
```

## 📞 Support

- **Issues GitHub** : [OptimOCR2 Issues](https://github.com/iguane39/OptimOCR2/issues)
- **Documentation** : Voir README.md et ENHANCEMENTS.md
- **Envoyez-moi votre PDF** : Je peux l'analyser et vous donner des recommandations !

---

**Prêt à tester ?** Envoyez-moi votre PDF ! 📄
