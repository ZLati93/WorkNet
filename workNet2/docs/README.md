# Documentation WorkNet

Ce dossier contient la documentation complète du projet WorkNet.

## 📄 Fichiers Disponibles

### Formats Markdown (Source)

- **`report.md`** - Rapport technique détaillé en Markdown
- **`presentation.md`** - Présentation du projet en Markdown

### Formats Binaires (À générer)

- **`rapport.docx`** - Rapport technique en format Word
- **`report.pdf`** - Rapport technique en format PDF
- **`presentation.pptx`** - Présentation en format PowerPoint

## 🔄 Conversion des Formats

### Markdown vers Word (.docx)

**Avec Pandoc :**
```bash
pandoc report.md -o rapport.docx
```

**Avec Markdown to Word (npm) :**
```bash
npm install -g markdown-to-word
markdown-to-word report.md -o rapport.docx
```

**En ligne :**
- Utiliser [Dillinger](https://dillinger.io/) ou [StackEdit](https://stackedit.io/)
- Exporter en Word

### Markdown vers PDF

**Avec Pandoc :**
```bash
pandoc report.md -o report.pdf --pdf-engine=xelatex
```

**Avec Markdown PDF (npm) :**
```bash
npm install -g markdown-pdf
markdown-pdf report.md -o report.pdf
```

**Via Word :**
1. Convertir Markdown → Word
2. Ouvrir dans Microsoft Word
3. Fichier → Enregistrer sous → PDF

### Markdown vers PowerPoint (.pptx)

**Avec Pandoc :**
```bash
pandoc presentation.md -o presentation.pptx
```

**Avec Marp (CLI) :**
```bash
npm install -g @marp-team/marp-cli
marp presentation.md -o presentation.pptx
```

**Manuellement :**
1. Ouvrir `presentation.md` dans un éditeur Markdown
2. Copier chaque slide
3. Créer une présentation PowerPoint
4. Coller le contenu slide par slide

## 📝 Structure du Rapport

Le rapport (`report.md`) contient :

1. Introduction
2. Architecture du Système
3. Technologies Utilisées
4. Structure du Projet
5. Fonctionnalités
6. Base de Données
7. API et Services
8. Sécurité
9. Tests
10. Déploiement
11. Conclusion

## 🎯 Structure de la Présentation

La présentation (`presentation.md`) contient 16 slides :

1. Titre
2. Problématique
3. Vue d'Ensemble
4. Architecture
5. Technologies
6. Fonctionnalités Clients
7. Fonctionnalités Freelancers
8. Sécurité
9. Tests
10. Déploiement
11. Structure du Projet
12. API REST
13. Base de Données
14. Performance
15. Roadmap
16. Conclusion

## 🛠 Outils Recommandés

### Pour la Conversion

- **Pandoc** : Convertisseur universel
  ```bash
  # Installation
  # macOS
  brew install pandoc
  
  # Ubuntu/Debian
  sudo apt-get install pandoc
  
  # Windows
  # Télécharger depuis https://pandoc.org/installing.html
  ```

- **Marp** : Pour les présentations
  ```bash
  npm install -g @marp-team/marp-cli
  ```

### Pour l'Édition

- **VS Code** avec extensions :
  - Markdown Preview Enhanced
  - Markdown PDF
  - Marp for VS Code

- **Typora** : Éditeur Markdown WYSIWYG

- **Obsidian** : Éditeur Markdown avec graph

## 📋 Instructions de Génération

### Rapport Word (.docx)

```bash
# Installer Pandoc
# Puis exécuter :
pandoc report.md -o rapport.docx \
  --reference-doc=template.docx \  # Optionnel : template personnalisé
  --toc \                          # Table des matières
  --highlight-style=tango          # Style de code
```

### Rapport PDF

```bash
# Avec Pandoc et LaTeX
pandoc report.md -o report.pdf \
  --pdf-engine=xelatex \
  --toc \
  --highlight-style=tango

# Ou convertir depuis Word
# Ouvrir rapport.docx dans Word → Enregistrer sous → PDF
```

### Présentation PowerPoint

```bash
# Avec Marp
marp presentation.md -o presentation.pptx

# Avec Pandoc
pandoc presentation.md -o presentation.pptx \
  --slide-level=2
```

## 🎨 Personnalisation

### Styles pour le Rapport

Créer un fichier `template.docx` avec :
- En-tête et pied de page
- Styles personnalisés
- Logo WorkNet
- Couleurs de la marque

### Thème pour la Présentation

Modifier `presentation.md` pour ajouter :
- Thème Marp personnalisé
- Images et logos
- Animations (si supporté)

## 📚 Ressources

- [Pandoc Documentation](https://pandoc.org/MANUAL.html)
- [Marp Documentation](https://marp.app/)
- [Markdown Guide](https://www.markdownguide.org/)

## ⚠️ Notes

- Les fichiers `.docx`, `.pdf` et `.pptx` existants peuvent être mis à jour en régénérant depuis les sources Markdown
- Toujours vérifier le formatage après conversion
- Les images doivent être dans un dossier `images/` relatif aux fichiers Markdown

