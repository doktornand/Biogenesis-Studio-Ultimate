# 🧬 Bio-Compiler Studio v3.0

Interface graphique temps réel et module CLI pour l'écosystème **Bio-Compiler** — un framework de compilation biologique inspiré par Hofstadter (boucles étranges), Conway (automates cellulaires) et Varela & Maturana (autopoïèse).

---

## 📦 Installation

```bash
# Dépendances obligatoires
pip install numpy

# Dépendances recommandées (visualisations)
pip install matplotlib networkx scipy

# Lancer l'application
python bio_compiler_studio.py
```

---

## 🚀 Utilisation

### Mode GUI (par défaut)

```bash
python bio_compiler_studio.py
# ou
python bio_compiler_studio.py --gui
```

L'interface s'ouvre avec 8 onglets :

| Onglet | Description |
|--------|-------------|
| 🧬 **Évolution** | Visualisation temps réel de la fitness, diversité, convergence. Contrôles interactifs (Start/Pause/Stop). |
| 🔬 **Protéines** | Graphe dirigé des 18 protéines avec héritage, phases cellulaires, opérons. |
| 🌳 **Phylogénie** | Dendrogramme évolutif (clustering hiérarchique sur distance ADN). |
| 🧪 **Épigénétique** | Heatmap des marqueurs H3K4me3, H3K27me3, H3K9me3... par protéine. |
| 🧫 **Plasmides** | Vue circulaire des 5 plasmides (PLM_LOGGER, WATCHDOG, TELOMERE...). |
| ✏️ **Éditeur ADN** | Éditeur avec coloration syntaxique des codons, transcription temps réel. |
| 🎛️ **Opérons** | État visuel des 6 opérons (OP_STRESS, OP_GROWTH, OP_REPLICATION...). |
| 📟 **Console** | Logs structurés avec filtres par niveau, export. |

### Mode CLI

```bash
# Évolution génétique
python bio_compiler_studio.py --cli --evolve --gens 100 --pop 50 --lang csharp

# Transcription manuelle
python bio_compiler_studio.py --cli --dna ATGTTTCTGCTC... --lang python --output code.py

# Générer les protéines .prot
python bio_compiler_studio.py --cli --generate-proteins --slot ./slot

# Avec coévolution et export phylogénie
python bio_compiler_studio.py --cli --evolve --coevolve --export-newick --export-history
```

---

## 🎛️ Architecture

```
bio_compiler_studio.py
├── BioCompilerEngine          # Wrapper thread-safe du moteur d'évolution
├── EvolutionPlot              # Graphique matplotlib temps réel
├── ProteinGraph               # Graphe NetworkX des dépendances
├── PhylogenyPlot              # Dendrogramme scipy
├── EpigeneticHeatmap          # Heatmap matplotlib
├── PlasmidView                # Vue circulaire matplotlib
├── DNAEditor                  # Éditeur Tkinter avec coloration
├── OperonPanel                # Panneau d'état des opérons
├── ConsoleWidget              # Console intégrée
└── BioCompilerStudio          # Application principale (Tkinter)
```

---

## 🧬 Fonctionnalités Avancées

- **Évolution temps réel** : Threading avec notifications par callbacks, pause/reprise
- **Graphe protéique interactif** : Héritage (extends), opérons, phases cellulaires colorées
- **Phylogénie Newick** : Export au format standard, clustering hiérarchique
- **Marqueurs épigénétiques** : H3K4me3 (activation), H3K27me3 (silençage), H3K9me3 (stress)...
- **Plasmides circulaires** : Représentation visuelle des structures circulaires/linéaires
- **Coloration ADN** : Codons start/stop, épigénétique, transposons, opérons
- **Coévolution** : Population hôte + population parasite
- **Niche partitioning** : Préservation de la diversité génétique

---

## 🎨 Thème

Thème sombre "laboratoire de biologie moléculaire" :
- Fond `#0a0e17` — profondeur nocturne
- Cyan `#06b6d4` — information, ADN
- Vert `#10b981` — fitness, croissance
- Magenta `#d946ef` — mutation, transposon
- Ambre `#f59e0b` — attention, opéron
- Rouge `#ef4444` — apoptose, erreur

---

## 📄 Licence

Projet éducatif inspiré par les travaux de Douglas Hofstadter (*Gödel, Escher, Bach*), John Conway (*Game of Life*), et Francisco Varela / Humberto Maturana (autopoïèse).
