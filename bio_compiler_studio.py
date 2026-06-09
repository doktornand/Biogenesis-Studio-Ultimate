#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  🧬 Bio-Compiler Studio v4.0 — GUI & CLI Multi-Langages                      ║
║  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  ║
║                                                                              ║
║  NOUVEAUTÉS v4.0 :                                                           ║
║  • Génération de protéines vers 5 langages (Python, C#, JS, Rust, Go)       ║
║  • Sélecteur de langage dans l'interface GUI                                ║
║  • Manifestes séparés par langage                                           ║
║  • Compatibilité totale avec prot_generator_multilang.py                    ║
║                                                                              ║
║  Interface graphique temps réel pour l'écosystème Bio-Compiler :             ║
║  • Visualisation de l'évolution génétique (fitness, diversité, convergence)  ║
║  • Graphe interactif des protéines et dépendances (héritage, opérons)        ║
║  • Arbre phylogénétique Newick avec coloration par fitness                   ║
║  • Heatmap des marqueurs épigénétiques (H3K4me3, H3K27me3, H3K9me3...)       ║
║  • Vue circulaire des plasmides et état des opérons                          ║
║  • Éditeur ADN avec coloration syntaxique et prévisualisation temps réel     ║
║  • Console intégrée avec logs structurés                                     ║
║                                                                              ║
║  Usage CLI :  python bio_compiler_studio_v4.py --cli [options]               ║
║  Usage GUI :  python bio_compiler_studio_v4.py --gui                         ║
║                                                                              ║
║  Dépendances : tkinter, matplotlib, numpy, networkx, scipy                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import json
import math
import os
import random
import re
import sys
import threading
import time
import tkinter as tk
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from tkinter import ttk, scrolledtext, filedialog, messagebox, font as tkfont
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ── Tentative d'import des dépendances optionnelles ──
try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from matplotlib.patches import Circle, FancyBboxPatch, Wedge, Rectangle
    from matplotlib.collections import LineCollection
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except ImportError:
    MATPLOTLIB_OK = False
    print("[WARN] matplotlib non disponible — visualisations désactivées")

try:
    import networkx as nx
    NETWORKX_OK = True
except ImportError:
    NETWORKX_OK = False
    print("[WARN] networkx non disponible — graphe de protéines simplifié")

try:
    from scipy.cluster.hierarchy import dendrogram, linkage
    from scipy.spatial.distance import pdist
    SCIPY_OK = True
except ImportError:
    SCIPY_OK = False
    print("[WARN] scipy non disponible — dendrogramme simplifié")

# ── Import du moteur Bio-Compiler ──
UPLOAD_DIR = Path(__file__).parent / "upload" if not Path("/mnt/agents/upload").exists() else Path("/mnt/agents/upload")
sys.path.insert(0, str(UPLOAD_DIR))
sys.path.insert(0, str(Path(__file__).parent))

BioCompiler = None
ProtEngine = None

def _load_module_from_path(module_name: str, file_name: str):
    """Charge un module Python depuis un chemin de fichier."""
    search_paths = [
        Path.cwd() / file_name,
        Path(__file__).parent / file_name,
        UPLOAD_DIR / file_name,
        Path("/mnt/agents/upload") / file_name,
    ]

    for path in search_paths:
        if path.exists():
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(module_name, str(path))
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    print(f"[OK] {file_name} chargé depuis {path}")
                    return module
            except Exception as e:
                print(f"[WARN] Erreur chargement {file_name} depuis {path}: {e}")
                continue

    print(f"[WARN] {file_name} introuvable dans: {[str(p) for p in search_paths]}")
    return None

BioCompiler = _load_module_from_path("bio_compiler", "Bio-Compiler_evolved.py")
ProtEngine = _load_module_from_path("prot_generator", "prot_generator_multilang.py")

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES & THÈME
# ══════════════════════════════════════════════════════════════════════════════

class Theme:
    BG_PRIMARY    = "#0a0e17"
    BG_SECONDARY  = "#111827"
    BG_TERTIARY   = "#1a2233"
    ACCENT_CYAN   = "#06b6d4"
    ACCENT_GREEN  = "#10b981"
    ACCENT_MAGENTA= "#d946ef"
    ACCENT_AMBER  = "#f59e0b"
    ACCENT_RED    = "#ef4444"
    ACCENT_VIOLET = "#8b5cf6"
    TEXT_PRIMARY  = "#f1f5f9"
    TEXT_SECONDARY= "#94a3b8"
    TEXT_MUTED    = "#64748b"
    BORDER        = "#1e293b"
    SUCCESS       = "#22c55e"
    WARNING       = "#eab308"

    PHASE_COLORS = {
        "G1": "#3b82f6", "G1_arrest": "#1d4ed8", "G1_S": "#60a5fa",
        "S": "#10b981", "S_checkpoint": "#059669", "S_late": "#34d399",
        "G2": "#f59e0b", "prophase": "#d97706", "metaphase": "#b45309",
        "M": "#ef4444", "apoptosis": "#7f1d1d", "apoptosis_late": "#450a0a",
        "G0_starvation": "#6b7280", "meta": "#d946ef", "G1_late": "#818cf8"
    }

    LANG_COLORS = {
        "python": "#3776AB",
        "csharp": "#239120",
        "javascript": "#F7DF1E",
        "rust": "#DEA584",
        "go": "#00ADD8",
    }

    EPIGENETIC_COLORS = {
        "h3k4me3_promoter": "#22c55e",
        "h3k27ac_enhancer": "#3b82f6", 
        "h3k36me3_transcribed": "#f59e0b",
        "h3k9me3_stress_silenced": "#ef4444",
        "h3s10ph_mitotic": "#d946ef",
        "h4k20me1": "#06b6d4",
        "clock_bmal1_acetylation": "#8b5cf6",
        "per_cry_phosphorylation": "#ec4899",
        "ezh2_prc2_complex": "#14b8a6",
        "swi_snf_brg1": "#f97316",
        "rna_pol1_active": "#84cc16",
        "pcna_sliding_clamp": "#6366f1",
        "h2ax_dna_damage": "#dc2626",
        "h3k9me3_silenced": "#991b1b",
        "tert_promoter_mutation": "#f43f5e",
        "self_referential_mark": "#a855f7"
    }

    # Langages supportés pour la génération de protéines
    SUPPORTED_LANGUAGES = ["python", "csharp", "javascript", "rust", "go"]


class LogLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    SUCCESS = auto()
    WARNING = auto()
    ERROR = auto()
    EVOLUTION = auto()
    BIO = auto()


class Logger:
    LEVEL_COLORS = {
        LogLevel.DEBUG: Theme.TEXT_MUTED,
        LogLevel.INFO: Theme.TEXT_SECONDARY,
        LogLevel.SUCCESS: Theme.SUCCESS,
        LogLevel.WARNING: Theme.WARNING,
        LogLevel.ERROR: Theme.ACCENT_RED,
        LogLevel.EVOLUTION: Theme.ACCENT_CYAN,
        LogLevel.BIO: Theme.ACCENT_GREEN,
    }
    LEVEL_EMOJI = {
        LogLevel.DEBUG: "🔍",
        LogLevel.INFO: "ℹ️",
        LogLevel.SUCCESS: "✅",
        LogLevel.WARNING: "⚠️",
        LogLevel.ERROR: "❌",
        LogLevel.EVOLUTION: "🧬",
        LogLevel.BIO: "🧪",
    }

    def __init__(self):
        self.observers = []
        self.history = []
        self._lock = threading.Lock()

    def add_observer(self, handler):
        self.observers.append(handler)

    def log(self, level, message):
        timestamp = time.time()
        with self._lock:
            self.history.append((timestamp, level, message))
            for handler in self.observers:
                try:
                    handler(timestamp, level, message)
                except Exception:
                    pass

    def debug(self, msg): self.log(LogLevel.DEBUG, msg)
    def info(self, msg): self.log(LogLevel.INFO, msg)
    def success(self, msg): self.log(LogLevel.SUCCESS, msg)
    def warning(self, msg): self.log(LogLevel.WARNING, msg)
    def error(self, msg): self.log(LogLevel.ERROR, msg)
    def evo(self, msg): self.log(LogLevel.EVOLUTION, msg)
    def bio(self, msg): self.log(LogLevel.BIO, msg)


logger = Logger()


# ══════════════════════════════════════════════════════════════════════════════
# WRAPPER DU MOTEUR BIO-COMPILER (thread-safe, multi-langages)
# ══════════════════════════════════════════════════════════════════════════════

class BioCompilerEngine:
    """Encapsule Bio-Compiler_evolved.py avec interface GUI et support multi-langages."""

    def __init__(self, config_path=None, target_lang="python"):
        self.config_path = config_path or str(UPLOAD_DIR / "proteome_config_949.json")
        self.config = json.loads(Path(self.config_path).read_text())
        self.target_lang = target_lang

        self.is_running = False
        self.is_paused = False
        self.current_generation = 0
        self.max_generations = 50
        self.population_size = 30
        self.mutation_rate = 0.02
        self.indel_rate = 0.005
        self.niche_count = 3
        self.coevolve = False
        self.target_keywords = ["for", "if", "try", "print"]
        self.language = "python"

        self.fitness_history = []
        self.best_dna = None
        self.best_fitness = 0.0
        self.population = []
        self.diversity_history = []
        self.phylogeny = []

        self.observers = []
        self._thread = None
        self._stop_event = threading.Event()

        self._engine = None
        self._transcriptor = None

        logger.info(f"Moteur Bio-Compiler initialisé (langue cible: {target_lang})")

    def set_target_language(self, lang: str):
        """Change le langage cible pour la transcription."""
        if lang in Theme.SUPPORTED_LANGUAGES:
            self.target_lang = lang
            self.language = lang
            # Réinitialiser les moteurs pour prendre en compte le nouveau langage
            self._engine = None
            self._transcriptor = None
            logger.info(f"Langage cible changé: {lang}")
        else:
            logger.warning(f"Langage non supporté: {lang}")

    def _get_engine(self):
        if self._engine is None and BioCompiler:
            loader = BioCompiler.ProteinLoader("./slot")
            genetic_code = BioCompiler.load_genetic_code()
            self._engine = BioCompiler.DNAEvolutionEngine(
                target_keywords=self.target_keywords,
                pop_size=self.population_size,
                gens=self.max_generations,
                mut_rate=self.mutation_rate,
                indel_rate=self.indel_rate,
                lang=self.target_lang,
                loader=loader,
                genetic_code=genetic_code,
                niche_count=self.niche_count,
                coevolve=self.coevolve,
            )
        return self._engine

    def _get_transcriptor(self):
        if self._transcriptor is None and BioCompiler:
            loader = BioCompiler.ProteinLoader("./slot")
            genetic_code = BioCompiler.load_genetic_code()
            self._transcriptor = BioCompiler.DNAToCodeTranscriptor(
                self.target_lang, loader, genetic_code
            )
        return self._transcriptor

    def add_observer(self, callback):
        self.observers.append(callback)

    def _notify(self, event_type, data):
        for obs in self.observers:
            try:
                obs(event_type, data)
            except Exception as e:
                logger.error(f"Erreur observateur: {e}")

    def start_evolution(self):
        if self.is_running:
            logger.warning("Évolution déjà en cours")
            return

        self.is_running = True
        self.is_paused = False
        self._stop_event.clear()
        self.fitness_history = []
        self.diversity_history = []
        self.phylogeny = []
        self.current_generation = 0

        self._thread = threading.Thread(target=self._evolution_loop, daemon=True)
        self._thread.start()
        logger.evo(f"Évolution démarrée: {self.max_generations} générations (langue: {self.target_lang})")

    def pause_evolution(self):
        self.is_paused = not self.is_paused
        logger.evo("Évolution " + ("en pause" if self.is_paused else "reprise"))

    def stop_evolution(self):
        self._stop_event.set()
        self.is_running = False
        logger.evo("Évolution arrêtée")

    def _evolution_loop(self):
        engine = self._get_engine()
        if not engine:
            logger.error("Moteur d'évolution non disponible")
            self.is_running = False
            return

        engine.gens = self.max_generations
        engine.pop_size = self.population_size
        engine.mut_rate = self.mutation_rate
        engine.indel_rate = self.indel_rate
        engine.niche_count = self.niche_count
        engine.coevolve = self.coevolve
        engine.target_kw = self.target_keywords

        engine.pop = [engine._rand() for _ in range(engine.pop_size)]
        self.population = engine.pop.copy()

        for dna in engine.pop[:5]:
            self.phylogeny.append({
                "dna": dna, "fitness": 0.0, "generation": 0,
                "parent_id": None, "node_id": f"root_{hash(dna) % 10000:04x}"
            })

        best_dna, best_fit = engine.pop[0], -1.0

        for g in range(engine.gens):
            if self._stop_event.is_set():
                break

            while self.is_paused and not self._stop_event.is_set():
                time.sleep(0.1)

            if self._stop_event.is_set():
                break

            entropy_bonuses = engine._entropy_bonus(engine.pop)
            parasite = random.choice(engine.parasite_pop) if engine.parasite_pop else None

            scored = sorted(
                [(dna, engine._fitness(dna, parasite) + entropy_bonuses.get(id(dna), 0))
                 for dna in engine.pop],
                key=lambda x: x[1], reverse=True
            )

            scored = engine._niche_partition(scored)
            best_dna, best_fit = scored[0]
            avg_fit = sum(f for _, f in scored) / len(scored)

            diversity = self._calculate_diversity([d for d, _ in scored])

            self.current_generation = g
            self.best_dna = best_dna
            self.best_fitness = best_fit
            self.population = [d for d, _ in scored]

            for rank, (dna, fit) in enumerate(scored[:3]):
                parent = self.phylogeny[-1] if self.phylogeny else None
                self.phylogeny.append({
                    "dna": dna, "fitness": fit, "generation": g,
                    "parent_id": parent["node_id"] if parent else None,
                    "node_id": f"gen{g}_r{rank}_{hash(dna) % 10000:04x}"
                })

            gen_data = {
                "generation": g,
                "best_fitness": best_fit,
                "avg_fitness": avg_fit,
                "diversity": diversity,
                "best_dna": best_dna,
                "population": [d for d, _ in scored[:5]],
                "pop_size": len(scored),
            }
            self.fitness_history.append(gen_data)
            self.diversity_history.append(diversity)

            self._notify("generation", gen_data)

            if g % 5 == 0:
                logger.evo(f"Gen {g:03d} | Fitness: {best_fit:.4f} | "
                          f"Diversité: {diversity:.3f} | Len: {len(best_dna)}bp")

            if best_fit >= 0.95:
                logger.success(f"🎯 Convergence anticipée à la génération {g}!")
                break

            elite_count = max(1, len(scored) // 10)
            new_pop = [s[0] for s in scored[:elite_count]]

            parents = [s[0] for s in scored[:max(2, len(scored) // 2)]]
            while len(new_pop) < engine.pop_size:
                p1, p2 = random.choices(parents, k=2)
                c1, c2 = engine._crossover_homologous(p1, p2)
                new_pop.extend([engine._mutate(c1), engine._mutate(c2)])

            engine.pop = new_pop[:engine.pop_size]

            if engine.coevolve and engine.parasite_pop:
                p_scored = sorted(
                    [(p, engine._fitness(p)) for p in engine.parasite_pop],
                    key=lambda x: x[1]
                )
                engine.parasite_pop = [p[0] for p in p_scored[:len(engine.parasite_pop)//2]]
                while len(engine.parasite_pop) < engine.pop_size // 2:
                    p1, p2 = random.choices(engine.parasite_pop, k=2)
                    c1, _ = engine._crossover_homologous(p1, p2)
                    engine.parasite_pop.append(engine._mutate(c1))

            time.sleep(0.05)

        self.is_running = False
        self._notify("finished", {
            "best_dna": best_dna,
            "best_fitness": best_fit,
            "generations": self.current_generation + 1,
            "history": self.fitness_history,
            "phylogeny": self.phylogeny,
        })
        logger.success(f"Évolution terminée. Fitness final: {best_fit:.4f}")

    def _calculate_diversity(self, population):
        if len(population) < 2:
            return 0.0
        total = 0
        count = 0
        for i, dna1 in enumerate(population):
            for dna2 in population[i+1:]:
                min_len = min(len(dna1), len(dna2))
                dist = sum(a != b for a, b in zip(dna1[:min_len], dna2[:min_len]))
                dist += abs(len(dna1) - len(dna2))
                total += dist
                count += 1
        return (total / count) / max(len(population[0]), 1) if count > 0 else 0.0

    def transcribe_dna(self, dna):
        transcriptor = self._get_transcriptor()
        if transcriptor:
            return transcriptor.transcribe(dna)
        return f"# Transcripteur non disponible (langue: {self.target_lang})"

    def generate_proteins(self, output_dir="./slot", target_lang=None):
        """Génère les fichiers protéines dans le langage spécifié."""
        if not ProtEngine:
            logger.error("Générateur de protéines non disponible")
            return {}
        
        lang = target_lang or self.target_lang
        try:
            # Utiliser le moteur multi-langages
            engine = ProtEngine.ProtEngine(
                self.config_path, output_dir,
                generation=self.current_generation,
                target_lang=lang
            )
            engine.generate_all()
            logger.success(f"{len(engine.cache)} protéines générées dans {output_dir} ({lang})")
            return engine.cache
        except Exception as e:
            logger.error(f"Erreur génération protéines: {e}")
            return {}


# ══════════════════════════════════════════════════════════════════════════════
# WIDGETS DE VISUALISATION MATPLOTLIB (inchangés, mais conservés pour complétude)
# ══════════════════════════════════════════════════════════════════════════════

class EvolutionPlot:
    def __init__(self, parent_frame):
        self.frame = parent_frame
        if not MATPLOTLIB_OK:
            self.canvas = None
            return

        self.fig = Figure(figsize=(8, 4), dpi=100, facecolor=Theme.BG_PRIMARY)
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        self.ax1.set_facecolor(Theme.BG_PRIMARY)
        self.ax2.set_facecolor(Theme.BG_PRIMARY)
        self.ax1.tick_params(colors=Theme.TEXT_SECONDARY)
        self.ax2.tick_params(colors=Theme.TEXT_SECONDARY)
        self.ax1.set_xlabel("Génération", color=Theme.TEXT_SECONDARY)
        self.ax1.set_ylabel("Fitness", color=Theme.ACCENT_GREEN)
        self.ax2.set_ylabel("Diversité", color=Theme.ACCENT_CYAN)

        self.line_best, = self.ax1.plot([], [], color=Theme.ACCENT_GREEN, linewidth=2, label="Meilleur fitness")
        self.line_avg, = self.ax1.plot([], [], color=Theme.ACCENT_AMBER, linewidth=1.5, alpha=0.7, label="Fitness moyen")
        self.line_div, = self.ax2.plot([], [], color=Theme.ACCENT_CYAN, linewidth=1, alpha=0.6, linestyle="--", label="Diversité")

        self.ax1.legend(loc="upper left", facecolor=Theme.BG_SECONDARY, edgecolor=Theme.BORDER, labelcolor=Theme.TEXT_SECONDARY)
        self.ax2.legend(loc="upper right", facecolor=Theme.BG_SECONDARY, edgecolor=Theme.BORDER, labelcolor=Theme.TEXT_SECONDARY)

        self.fig.tight_layout()

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update(self, history):
        if not self.canvas or not history:
            return

        gens = [h["generation"] for h in history]
        best = [h["best_fitness"] for h in history]
        avg = [h["avg_fitness"] for h in history]
        div = [h.get("diversity", 0) for h in history]

        self.line_best.set_data(gens, best)
        self.line_avg.set_data(gens, avg)
        self.line_div.set_data(gens, div)

        self.ax1.relim()
        self.ax1.autoscale_view()
        self.ax2.relim()
        self.ax2.autoscale_view()

        self.canvas.draw_idle()


class ProteinGraph:
    def __init__(self, parent_frame, config):
        self.frame = parent_frame
        self.config = config
        if not MATPLOTLIB_OK or not NETWORKX_OK:
            self.canvas = None
            return

        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor=Theme.BG_PRIMARY)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(Theme.BG_PRIMARY)
        self.ax.axis("off")

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._build_graph()

    def _build_graph(self):
        if not NETWORKX_OK:
            return

        G = nx.DiGraph()
        proteins = self.config.get("proteins", [])

        for prot in proteins:
            pid = prot["id"]
            phase = prot.get("meta", {}).get("cell_phase", "unknown")
            color = Theme.PHASE_COLORS.get(phase, Theme.TEXT_MUTED)
            weight = prot.get("meta", {}).get("weight", 1.0)
            G.add_node(pid, color=color, weight=weight, phase=phase, data=prot)

        for prot in proteins:
            if prot.get("extends"):
                G.add_edge(prot["extends"], prot["id"], 
                          relation="héritage", color=Theme.ACCENT_CYAN, width=2)

        for operon in self.config.get("operons", []):
            oid = operon["id"]
            G.add_node(oid, color=Theme.ACCENT_AMBER, weight=1.5, 
                      phase="operon", data=operon)
            for gene in operon.get("genes", []):
                if gene in G:
                    G.add_edge(oid, gene, relation="opéron", 
                              color=Theme.ACCENT_AMBER, width=1.5, style="dashed")

        for plasmid in self.config.get("plasmids", []):
            pid = plasmid["id"]
            G.add_node(pid, color=Theme.ACCENT_VIOLET, weight=1.2,
                      phase="plasmid", data=plasmid)

        self.G = G
        self._draw_graph()

    def _draw_graph(self):
        self.ax.clear()
        self.ax.set_facecolor(Theme.BG_PRIMARY)
        self.ax.axis("off")

        if not hasattr(self, 'G'):
            return

        pos = nx.spring_layout(self.G, k=2, iterations=50, seed=42)

        node_colors = [self.G.nodes[n].get("color", Theme.TEXT_SECONDARY) for n in self.G.nodes()]
        node_sizes = [self.G.nodes[n].get("weight", 1.0) * 800 for n in self.G.nodes()]

        nx.draw_networkx_nodes(self.G, pos, ax=self.ax, node_color=node_colors,
                              node_size=node_sizes, alpha=0.9, edgecolors=Theme.BORDER)

        edges = list(self.G.edges())
        edge_colors = [self.G[u][v].get("color", Theme.TEXT_MUTED) for u, v in edges]
        edge_widths = [self.G[u][v].get("width", 1) for u, v in edges]

        nx.draw_networkx_edges(self.G, pos, ax=self.ax, edge_color=edge_colors,
                              width=edge_widths, alpha=0.6, arrows=True,
                              arrowsize=15, connectionstyle="arc3,rad=0.1")

        nx.draw_networkx_labels(self.G, pos, ax=self.ax, font_size=8,
                               font_color=Theme.TEXT_PRIMARY, font_weight="bold")

        self.ax.set_title("Réseau Protéique — Dépendances & Héritage", 
                         color=Theme.TEXT_PRIMARY, fontsize=12, pad=20)
        self.canvas.draw_idle()


class PhylogenyPlot:
    def __init__(self, parent_frame):
        self.frame = parent_frame
        if not MATPLOTLIB_OK or not SCIPY_OK:
            self.canvas = None
            return

        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor=Theme.BG_PRIMARY)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(Theme.BG_PRIMARY)
        self.ax.tick_params(colors=Theme.TEXT_SECONDARY)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def update(self, phylogeny):
        if not self.canvas or not phylogeny or len(phylogeny) < 3:
            return

        self.ax.clear()
        self.ax.set_facecolor(Theme.BG_PRIMARY)
        self.ax.tick_params(colors=Theme.TEXT_SECONDARY)

        dnas = [p["dna"] for p in phylogeny]
        fitnesses = [p["fitness"] for p in phylogeny]

        n = len(dnas)
        dist_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(i+1, n):
                min_len = min(len(dnas[i]), len(dnas[j]))
                dist = sum(a != b for a, b in zip(dnas[i][:min_len], dnas[j][:min_len]))
                dist += abs(len(dnas[i]) - len(dnas[j]))
                dist_matrix[i, j] = dist
                dist_matrix[j, i] = dist

        condensed = pdist(dist_matrix)
        Z = linkage(condensed, method="average")

        dendrogram(Z, ax=self.ax, orientation="top", 
                  color_threshold=0.7 * max(Z[:, 2]),
                  above_threshold_color=Theme.TEXT_MUTED,
                  leaf_font_size=8, leaf_rotation=90)

        self.ax.set_title("Phylogénie — Arbre évolutif (distance ADN)",
                         color=Theme.TEXT_PRIMARY, fontsize=12)
        self.ax.set_xlabel("Individus", color=Theme.TEXT_SECONDARY)
        self.ax.set_ylabel("Distance génétique", color=Theme.TEXT_SECONDARY)

        self.canvas.draw_idle()


class EpigeneticHeatmap:
    def __init__(self, parent_frame, config):
        self.frame = parent_frame
        self.config = config
        if not MATPLOTLIB_OK:
            self.canvas = None
            return

        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor=Theme.BG_PRIMARY)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(Theme.BG_PRIMARY)
        self.ax.tick_params(colors=Theme.TEXT_SECONDARY)

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._draw_heatmap()

    def _draw_heatmap(self):
        proteins = self.config.get("proteins", [])

        all_markers = set()
        for prot in proteins:
            all_markers.update(prot.get("epigenetic_markers", []))
        all_markers = sorted(all_markers)

        if not all_markers:
            self.ax.text(0.5, 0.5, "Aucun marqueur épigénétique défini",
                        ha="center", va="center", color=Theme.TEXT_SECONDARY,
                        transform=self.ax.transAxes, fontsize=12)
            self.canvas.draw_idle()
            return

        matrix = np.zeros((len(proteins), len(all_markers)))
        for i, prot in enumerate(proteins):
            markers = prot.get("epigenetic_markers", [])
            for j, marker in enumerate(all_markers):
                matrix[i, j] = 1.0 if marker in markers else 0.0

        im = self.ax.imshow(matrix, cmap="YlOrRd", aspect="auto", 
                           interpolation="nearest")

        self.ax.set_xticks(range(len(all_markers)))
        self.ax.set_xticklabels(all_markers, rotation=45, ha="right",
                               color=Theme.TEXT_SECONDARY, fontsize=8)
        self.ax.set_yticks(range(len(proteins)))
        self.ax.set_yticklabels([p["id"] for p in proteins],
                               color=Theme.TEXT_SECONDARY, fontsize=8)

        self.ax.set_title("Marqueurs Épigénétiques — Profil par Protéine",
                         color=Theme.TEXT_PRIMARY, fontsize=12, pad=20)

        cbar = self.fig.colorbar(im, ax=self.ax, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(colors=Theme.TEXT_SECONDARY)
        cbar.set_label("Présence", color=Theme.TEXT_SECONDARY)

        self.fig.tight_layout()
        self.canvas.draw_idle()


class PlasmidView:
    def __init__(self, parent_frame, config):
        self.frame = parent_frame
        self.config = config
        if not MATPLOTLIB_OK:
            self.canvas = None
            return

        self.fig = Figure(figsize=(8, 5), dpi=100, facecolor=Theme.BG_PRIMARY)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(Theme.BG_PRIMARY)
        self.ax.axis("equal")
        self.ax.axis("off")

        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._draw_plasmids()

    def _draw_plasmids(self):
        plasmids = self.config.get("plasmids", [])
        if not plasmids:
            self.ax.text(0, 0, "Aucun plasmide défini", ha="center", va="center",
                        color=Theme.TEXT_SECONDARY, fontsize=12)
            self.canvas.draw_idle()
            return

        self.ax.clear()
        self.ax.set_facecolor(Theme.BG_PRIMARY)
        self.ax.axis("equal")
        self.ax.axis("off")

        n = len(plasmids)
        radius = 1.0
        spacing = 2.5

        for idx, plasmid in enumerate(plasmids):
            pid = plasmid["id"]
            circular = plasmid.get("circular", False)
            copy_num = plasmid.get("copy_number", 1)

            angle = 2 * math.pi * idx / n
            cx = spacing * math.cos(angle)
            cy = spacing * math.sin(angle)

            if circular:
                circle = Circle((cx, cy), radius, fill=False, 
                              edgecolor=Theme.ACCENT_VIOLET, linewidth=3)
                self.ax.add_patch(circle)
            else:
                rect = FancyBboxPatch((cx - radius, cy - 0.3), 2*radius, 0.6,
                                     boxstyle="round,pad=0.1",
                                     facecolor=Theme.BG_TERTIARY,
                                     edgecolor=Theme.ACCENT_VIOLET, linewidth=2)
                self.ax.add_patch(rect)

            self.ax.text(cx, cy + radius + 0.3, f"{pid} (×{copy_num})",
                        ha="center", va="bottom", color=Theme.TEXT_PRIMARY,
                        fontsize=9, fontweight="bold")

            seq = plasmid.get("sequence", [])
            if seq:
                desc = plasmid.get("description", "")[:40]
                self.ax.text(cx, cy - radius - 0.3, desc,
                            ha="center", va="top", color=Theme.TEXT_SECONDARY,
                            fontsize=7, style="italic")

        self.ax.set_title("Plasmides — Structures Circulaires & Linéaires",
                         color=Theme.TEXT_PRIMARY, fontsize=12, pad=20)
        self.ax.set_xlim(-spacing - 2, spacing + 2)
        self.ax.set_ylim(-spacing - 2, spacing + 2)

        self.canvas.draw_idle()


# ══════════════════════════════════════════════════════════════════════════════
# WIDGETS SPÉCIALISÉS
# ══════════════════════════════════════════════════════════════════════════════

class DNAEditor:
    def __init__(self, parent_frame, on_change=None):
        self.frame = parent_frame
        self.on_change = on_change

        container = tk.Frame(parent_frame, bg=Theme.BG_SECONDARY)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(container, text="🧬 Éditeur de Séquence ADN", 
                bg=Theme.BG_SECONDARY, fg=Theme.ACCENT_CYAN,
                font=("Consolas", 11, "bold")).pack(anchor="w", padx=5, pady=5)

        text_frame = tk.Frame(container, bg=Theme.BG_SECONDARY)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.text = tk.Text(text_frame, wrap=tk.NONE, height=10,
                           bg=Theme.BG_PRIMARY, fg=Theme.TEXT_PRIMARY,
                           insertbackground=Theme.ACCENT_CYAN,
                           font=("Consolas", 10), padx=10, pady=10,
                           selectbackground=Theme.ACCENT_CYAN,
                           selectforeground=Theme.BG_PRIMARY)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(text_frame, command=self.text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=scrollbar.set)

        btn_frame = tk.Frame(container, bg=Theme.BG_SECONDARY)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)

        self._make_btn(btn_frame, "🎲 Aléatoire", self._random_dna, Theme.ACCENT_MAGENTA)
        self._make_btn(btn_frame, "▶️ Transcrire", self._transcribe, Theme.ACCENT_GREEN)
        self._make_btn(btn_frame, "💾 Sauver", self._save_dna, Theme.ACCENT_CYAN)
        self._make_btn(btn_frame, "📂 Charger", self._load_dna, Theme.ACCENT_AMBER)

        self.result = tk.Text(container, wrap=tk.WORD, height=8,
                             bg=Theme.BG_PRIMARY, fg=Theme.TEXT_SECONDARY,
                             font=("Consolas", 9), padx=10, pady=10,
                             state=tk.DISABLED)
        self.result.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self._setup_tags()
        self.text.bind("<KeyRelease>", self._on_key_release)

    def _make_btn(self, parent, text, cmd, color):
        btn = tk.Button(parent, text=text, command=cmd,
                       bg=Theme.BG_TERTIARY, fg=color,
                       activebackground=color, activeforeground=Theme.BG_PRIMARY,
                       relief=tk.FLAT, font=("Consolas", 9),
                       cursor="hand2", padx=10, pady=3)
        btn.pack(side=tk.LEFT, padx=3)
        return btn

    def _setup_tags(self):
        colors = {
            "ATG": Theme.ACCENT_GREEN,
            "TAA": Theme.ACCENT_RED, "TAG": Theme.ACCENT_RED, "TGA": Theme.ACCENT_RED,
            "CGG": Theme.ACCENT_MAGENTA, "CGC": Theme.ACCENT_MAGENTA,
            "TTA": Theme.ACCENT_VIOLET, "TTG": Theme.ACCENT_VIOLET,
            "GAT": Theme.ACCENT_AMBER, "GAC": Theme.ACCENT_AMBER,
        }
        for codon, color in colors.items():
            self.text.tag_config(codon, foreground=color, font=("Consolas", 10, "bold"))

    def _on_key_release(self, event=None):
        self._colorize()
        if self.on_change:
            self.on_change(self.get_dna())

    def _colorize(self):
        content = self.text.get("1.0", tk.END).strip()
        self.text.tag_remove("ATG", "1.0", tk.END)
        self.text.tag_remove("TAA", "1.0", tk.END)
        self.text.tag_remove("TAG", "1.0", tk.END)
        self.text.tag_remove("TGA", "1.0", tk.END)
        self.text.tag_remove("CGG", "1.0", tk.END)
        self.text.tag_remove("CGC", "1.0", tk.END)
        self.text.tag_remove("TTA", "1.0", tk.END)
        self.text.tag_remove("TTG", "1.0", tk.END)
        self.text.tag_remove("GAT", "1.0", tk.END)
        self.text.tag_remove("GAC", "1.0", tk.END)

        for codon in ["ATG", "TAA", "TAG", "TGA", "CGG", "CGC", "TTA", "TTG", "GAT", "GAC"]:
            start = "1.0"
            while True:
                pos = self.text.search(codon, start, tk.END, nocase=1)
                if not pos:
                    break
                end = f"{pos}+{len(codon)}c"
                self.text.tag_add(codon, pos, end)
                start = end

    def _random_dna(self):
        length = random.randint(36, 60)
        length = (length // 3) * 3
        bases = "ATCG"
        dna = "".join(random.choice(bases) for _ in range(length))
        self.set_dna(dna)
        logger.bio(f"Séquence aléatoire générée: {len(dna)}bp")

    def _transcribe(self):
        dna = self.get_dna()
        if len(dna) < 3:
            self._set_result("Séquence trop courte (min 3bp)")
            return

        if BioCompiler:
            try:
                loader = BioCompiler.ProteinLoader("./slot")
                genetic_code = BioCompiler.load_genetic_code()
                # Utiliser le langage courant du moteur
                current_lang = getattr(self, 'current_lang', 'python')
                transcriptor = BioCompiler.DNAToCodeTranscriptor(current_lang, loader, genetic_code)
                code = transcriptor.transcribe(dna)
                self._set_result(code)
                logger.bio(f"Transcription réussie: {len(code)} caractères ({current_lang})")
            except Exception as e:
                self._set_result(f"Erreur transcription: {e}")
                logger.error(f"Transcription: {e}")
        else:
            self._set_result("# Moteur Bio-Compiler non disponible")

    def _save_dna(self):
        dna = self.get_dna()
        path = filedialog.asksaveasfilename(defaultextension=".fasta",
                                           filetypes=[("FASTA", "*.fasta"), ("Texte", "*.txt")])
        if path:
            with open(path, "w") as f:
                f.write(f">BioCompiler_Sequence_{len(dna)}bp\n{dna}\n")
            logger.success(f"Séquence sauvegardée: {path}")

    def _load_dna(self):
        path = filedialog.askopenfilename(filetypes=[("FASTA", "*.fasta"), ("Texte", "*.txt"), ("Tous", "*.*")])
        if path:
            with open(path) as f:
                lines = f.readlines()
            dna = "".join(l.strip() for l in lines if not l.startswith(">"))
            self.set_dna(dna)
            logger.success(f"Séquence chargée: {path}")

    def get_dna(self):
        return self.text.get("1.0", tk.END).strip().upper().replace(" ", "").replace("\n", "")

    def set_dna(self, dna):
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", dna)
        self._colorize()
        if self.on_change:
            self.on_change(dna)

    def _set_result(self, text):
        self.result.config(state=tk.NORMAL)
        self.result.delete("1.0", tk.END)
        self.result.insert("1.0", text)
        self.result.config(state=tk.DISABLED)


class ConsoleWidget:
    def __init__(self, parent_frame):
        self.frame = parent_frame

        header = tk.Frame(parent_frame, bg=Theme.BG_SECONDARY)
        header.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(header, text="📟 Console Système", 
                bg=Theme.BG_SECONDARY, fg=Theme.TEXT_PRIMARY,
                font=("Consolas", 11, "bold")).pack(side=tk.LEFT)

        self._make_btn(header, "🗑️ Effacer", self.clear, Theme.TEXT_MUTED)
        self._make_btn(header, "💾 Export", self.export, Theme.ACCENT_CYAN)

        self.text = scrolledtext.ScrolledText(
            parent_frame, wrap=tk.WORD, height=12,
            bg=Theme.BG_PRIMARY, fg=Theme.TEXT_SECONDARY,
            font=("Consolas", 9), padx=10, pady=10,
            insertbackground=Theme.ACCENT_CYAN,
            selectbackground=Theme.ACCENT_CYAN,
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.text.config(state=tk.DISABLED)

        for level, color in Logger.LEVEL_COLORS.items():
            self.text.tag_config(level.name, foreground=color)

    def _make_btn(self, parent, text, cmd, color):
        btn = tk.Button(parent, text=text, command=cmd,
                       bg=Theme.BG_TERTIARY, fg=color,
                       activebackground=color, activeforeground=Theme.BG_PRIMARY,
                       relief=tk.FLAT, font=("Consolas", 8),
                       cursor="hand2", padx=8, pady=2)
        btn.pack(side=tk.RIGHT, padx=3)
        return btn

    def append(self, timestamp, level, message):
        self.text.config(state=tk.NORMAL)
        emoji = Logger.LEVEL_EMOJI.get(level, "")
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        line = f"[{time_str}] {emoji} {message}\n"
        self.text.insert(tk.END, line, level.name)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension=".log",
                                           filetypes=[("Log", "*.log"), ("Texte", "*.txt")])
        if path:
            with open(path, "w") as f:
                for ts, level, msg in logger.history:
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
                    f.write(f"[{time_str}] {level.name}: {msg}\n")
            logger.success(f"Logs exportés: {path}")


class OperonPanel:
    def __init__(self, parent_frame, config):
        self.frame = parent_frame
        self.config = config
        self.operons = config.get("operons", [])

        tk.Label(parent_frame, text="🎛️ Opérons & Régulation", 
                bg=Theme.BG_SECONDARY, fg=Theme.ACCENT_AMBER,
                font=("Consolas", 11, "bold")).pack(anchor="w", padx=5, pady=5)

        self.operon_frames = {}
        for operon in self.operons:
            oid = operon["id"]
            frame = tk.Frame(parent_frame, bg=Theme.BG_TERTIARY, padx=10, pady=5)
            frame.pack(fill=tk.X, padx=5, pady=2)

            self.status_canvas = tk.Canvas(frame, width=16, height=16,
                                          bg=Theme.BG_TERTIARY, highlightthickness=0)
            self.status_canvas.pack(side=tk.LEFT, padx=5)
            self.status_circle = self.status_canvas.create_oval(2, 2, 14, 14, 
                                                                fill=Theme.TEXT_MUTED)

            info_frame = tk.Frame(frame, bg=Theme.BG_TERTIARY)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            tk.Label(info_frame, text=oid, bg=Theme.BG_TERTIARY,
                    fg=Theme.TEXT_PRIMARY, font=("Consolas", 10, "bold")).pack(anchor="w")

            cond = operon.get("promoter_condition", "N/A")
            genes = ", ".join(operon.get("genes", []))
            repressor = operon.get("repressor", "Aucun")

            tk.Label(info_frame, 
                    text=f"Promoteur: {cond} | Gènes: {genes} | Répresseur: {repressor}",
                    bg=Theme.BG_TERTIARY, fg=Theme.TEXT_SECONDARY,
                    font=("Consolas", 8)).pack(anchor="w")

            self.operon_frames[oid] = {
                "frame": frame,
                "canvas": self.status_canvas,
                "circle": self.status_circle,
                "data": operon,
            }

    def update_state(self, cellular_state, cell_generation):
        for oid, widgets in self.operon_frames.items():
            operon = widgets["data"]
            cond = operon.get("promoter_condition", "False")

            active = False
            try:
                ns = {"state_var": cellular_state, "cell_generation": cell_generation}
                active = eval(cond, {"__builtins__": {}}, ns)
            except Exception:
                active = False

            color = Theme.ACCENT_GREEN if active else Theme.ACCENT_RED
            widgets["canvas"].itemconfig(widgets["circle"], fill=color)


# ══════════════════════════════════════════════════════════════════════════════
# CLASSE PRINCIPALE DE L'APPLICATION GUI (VERSION MULTI-LANGAGES)
# ══════════════════════════════════════════════════════════════════════════════

class BioCompilerStudio:
    """Application GUI principale — Bio-Compiler Studio v4.0 Multi-Langages"""

    def __init__(self, config_path=None):
        self.config_path = config_path or str(UPLOAD_DIR / "proteome_config_949.json")
        self.config = json.loads(Path(self.config_path).read_text())

        # Moteur avec langage par défaut
        self.engine = BioCompilerEngine(self.config_path, target_lang="python")
        self.engine.add_observer(self._on_engine_event)

        # Fenêtre principale
        self.root = tk.Tk()
        self.root.title("🧬 Bio-Compiler Studio v4.0 — Multi-Langages")
        self.root.geometry("1450x950")
        self.root.configure(bg=Theme.BG_PRIMARY)

        self._setup_styles()
        self._build_menu()
        self._build_toolbar()
        self._build_main_area()
        self._build_statusbar()

        logger.add_observer(self._on_log)
        self._refresh_interval = 100
        self._schedule_refresh()

        logger.success("Bio-Compiler Studio v4.0 démarré (multi-langages)")

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("TNotebook", background=Theme.BG_PRIMARY, borderwidth=0)
        style.configure("TNotebook.Tab", background=Theme.BG_SECONDARY,
                       foreground=Theme.TEXT_SECONDARY, padding=[15, 5],
                       font=("Consolas", 10))
        style.map("TNotebook.Tab",
                 background=[("selected", Theme.BG_TERTIARY)],
                 foreground=[("selected", Theme.ACCENT_CYAN)])

        style.configure("TFrame", background=Theme.BG_PRIMARY)
        style.configure("TLabel", background=Theme.BG_PRIMARY, foreground=Theme.TEXT_SECONDARY)
        style.configure("TButton", background=Theme.BG_TERTIARY, foreground=Theme.TEXT_PRIMARY)
        style.configure("Horizontal.TProgressbar", background=Theme.ACCENT_GREEN,
                       troughcolor=Theme.BG_SECONDARY)

    def _build_menu(self):
        menubar = tk.Menu(self.root, bg=Theme.BG_SECONDARY, fg=Theme.TEXT_PRIMARY,
                         activebackground=Theme.BG_TERTIARY, activeforeground=Theme.ACCENT_CYAN)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0, bg=Theme.BG_SECONDARY,
                           fg=Theme.TEXT_PRIMARY, activebackground=Theme.BG_TERTIARY)
        file_menu.add_command(label="📂 Charger Configuration", command=self._load_config)
        file_menu.add_command(label="💾 Sauver Configuration", command=self._save_config)
        file_menu.add_separator()
        file_menu.add_command(label="🧬 Générer Protéines", command=self._generate_proteins)
        file_menu.add_separator()
        file_menu.add_command(label="❌ Quitter", command=self.root.quit)
        menubar.add_cascade(label="Fichier", menu=file_menu)

        evo_menu = tk.Menu(menubar, tearoff=0, bg=Theme.BG_SECONDARY,
                          fg=Theme.TEXT_PRIMARY, activebackground=Theme.BG_TERTIARY)
        evo_menu.add_command(label="▶️ Démarrer", command=self._start_evolution)
        evo_menu.add_command(label="⏸️ Pause/Reprendre", command=self._pause_evolution)
        evo_menu.add_command(label="⏹️ Arrêter", command=self._stop_evolution)
        evo_menu.add_separator()
        evo_menu.add_command(label="⚙️ Paramètres...", command=self._show_params)
        menubar.add_cascade(label="Évolution", menu=evo_menu)

        lang_menu = tk.Menu(menubar, tearoff=0, bg=Theme.BG_SECONDARY,
                           fg=Theme.TEXT_PRIMARY, activebackground=Theme.BG_TERTIARY)
        for lang in Theme.SUPPORTED_LANGUAGES:
            lang_menu.add_command(label=f"🐍 {lang.upper()}" if lang == "python" else
                                 f"🟦 {lang.upper()}" if lang == "csharp" else
                                 f"🟨 {lang.upper()}" if lang == "javascript" else
                                 f"🦀 {lang.upper()}" if lang == "rust" else
                                 f"🔵 {lang.upper()}",
                                 command=lambda l=lang: self._change_language(l))
        menubar.add_cascade(label="🌐 Langage", menu=lang_menu)

        export_menu = tk.Menu(menubar, tearoff=0, bg=Theme.BG_SECONDARY,
                             fg=Theme.TEXT_PRIMARY, activebackground=Theme.BG_TERTIARY)
        export_menu.add_command(label="📊 Graphique Fitness (PNG)", command=self._export_fitness)
        export_menu.add_command(label="🌳 Phylogénie (Newick)", command=self._export_newick)
        export_menu.add_command(label="🧬 Séquence (FASTA)", command=self._export_fasta)
        export_menu.add_command(label="📜 Code Généré", command=self._export_code)
        menubar.add_cascade(label="Export", menu=export_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=Theme.BG_SECONDARY,
                           fg=Theme.TEXT_PRIMARY, activebackground=Theme.BG_TERTIARY)
        help_menu.add_command(label="📖 Documentation", command=self._show_docs)
        help_menu.add_command(label="ℹ️ À propos", command=self._show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)

    def _build_toolbar(self):
        toolbar = tk.Frame(self.root, bg=Theme.BG_SECONDARY, height=50)
        toolbar.pack(fill=tk.X, padx=0, pady=0)
        toolbar.pack_propagate(False)

        buttons = [
            ("▶️ Start", self._start_evolution, Theme.ACCENT_GREEN),
            ("⏸️ Pause", self._pause_evolution, Theme.ACCENT_AMBER),
            ("⏹️ Stop", self._stop_evolution, Theme.ACCENT_RED),
            ("🧬 Protéines", self._generate_proteins, Theme.ACCENT_VIOLET),
            ("🎲 Random DNA", self._random_dna, Theme.ACCENT_MAGENTA),
        ]

        for text, cmd, color in buttons:
            btn = tk.Button(toolbar, text=text, command=cmd,
                           bg=Theme.BG_TERTIARY, fg=color,
                           activebackground=color, activeforeground=Theme.BG_PRIMARY,
                           relief=tk.FLAT, font=("Consolas", 10, "bold"),
                           cursor="hand2", padx=15, pady=5)
            btn.pack(side=tk.LEFT, padx=5, pady=8)

        # Sélecteur de langage dans la toolbar
        tk.Label(toolbar, text="🎯 Langue:", bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT_SECONDARY, font=("Consolas", 10)).pack(side=tk.RIGHT, padx=(0, 5))

        self.lang_var = tk.StringVar(value="python")
        lang_combo = ttk.Combobox(toolbar, textvariable=self.lang_var,
                                  values=Theme.SUPPORTED_LANGUAGES,
                                  state="readonly", width=10)
        lang_combo.pack(side=tk.RIGHT, padx=(0, 15))
        lang_combo.bind("<<ComboboxSelected>>", lambda e: self._change_language(self.lang_var.get()))

        self.status_label = tk.Label(toolbar, text="⏹️ Prêt",
                                    bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED,
                                    font=("Consolas", 10))
        self.status_label.pack(side=tk.RIGHT, padx=15)

        self.progress = ttk.Progressbar(toolbar, mode="determinate", length=200)
        self.progress.pack(side=tk.RIGHT, padx=10, pady=15)

    def _build_main_area(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.tab_evolution = tk.Frame(self.notebook, bg=Theme.BG_PRIMARY)
        self.notebook.add(self.tab_evolution, text=" 🧬 Évolution ")
        self._build_evolution_tab()

        self.tab_proteins = tk.Frame(self.notebook, bg=Theme.BG_PRIMARY)
        self.notebook.add(self.tab_proteins, text=" 🔬 Protéines ")
        self._build_proteins_tab()

        self.tab_phylo = tk.Frame(self.notebook, bg=Theme.BG_PRIMARY)
        self.notebook.add(self.tab_phylo, text=" 🌳 Phylogénie ")
        self._build_phylo_tab()

        self.tab_epi = tk.Frame(self.notebook, bg=Theme.BG_PRIMARY)
        self.notebook.add(self.tab_epi, text=" 🧪 Épigénétique ")
        self._build_epigenetic_tab()

        self.tab_plasmids = tk.Frame(self.notebook, bg=Theme.BG_PRIMARY)
        self.notebook.add(self.tab_plasmids, text=" 🧫 Plasmides ")
        self._build_plasmids_tab()

        self.tab_editor = tk.Frame(self.notebook, bg=Theme.BG_PRIMARY)
        self.notebook.add(self.tab_editor, text=" ✏️ Éditeur ADN ")
        self._build_editor_tab()

        self.tab_operons = tk.Frame(self.notebook, bg=Theme.BG_PRIMARY)
        self.notebook.add(self.tab_operons, text=" 🎛️ Opérons ")
        self._build_operons_tab()

        self.tab_console = tk.Frame(self.notebook, bg=Theme.BG_PRIMARY)
        self.notebook.add(self.tab_console, text=" 📟 Console ")
        self._build_console_tab()

    def _build_evolution_tab(self):
        control_frame = tk.Frame(self.tab_evolution, bg=Theme.BG_SECONDARY, width=300)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        control_frame.pack_propagate(False)

        tk.Label(control_frame, text="⚙️ Paramètres d'Évolution",
                bg=Theme.BG_SECONDARY, fg=Theme.ACCENT_CYAN,
                font=("Consolas", 11, "bold")).pack(anchor="w", padx=10, pady=10)

        self._build_param_slider(control_frame, "Générations", 10, 200, 
                                self.engine.max_generations, "max_generations")
        self._build_param_slider(control_frame, "Population", 10, 100,
                                self.engine.population_size, "population_size")
        self._build_param_slider(control_frame, "Taux Mutation (%)", 0, 20,
                                int(self.engine.mutation_rate * 100), "mutation_rate", scale=0.01)
        self._build_param_slider(control_frame, "Taux Indel (%)", 0, 10,
                                int(self.engine.indel_rate * 100), "indel_rate", scale=0.01)
        self._build_param_slider(control_frame, "Nic Écologiques", 1, 10,
                                self.engine.niche_count, "niche_count")

        self.coevolve_var = tk.BooleanVar(value=self.engine.coevolve)
        tk.Checkbutton(control_frame, text="🦠 Coévolution (hôte/parasite)",
                      variable=self.coevolve_var, bg=Theme.BG_SECONDARY,
                      fg=Theme.TEXT_SECONDARY, selectcolor=Theme.BG_TERTIARY,
                      activebackground=Theme.BG_SECONDARY,
                      command=lambda: setattr(self.engine, "coevolve", self.coevolve_var.get()))

        tk.Label(control_frame, text="🎯 Mots-clés cibles:",
                bg=Theme.BG_SECONDARY, fg=Theme.TEXT_SECONDARY,
                font=("Consolas", 9)).pack(anchor="w", padx=10, pady=(15, 5))
        self.keywords_entry = tk.Entry(control_frame, bg=Theme.BG_PRIMARY,
                                      fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_CYAN,
                                      font=("Consolas", 9))
        self.keywords_entry.insert(0, " ".join(self.engine.target_keywords))
        self.keywords_entry.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(control_frame, text="📊 Statistiques",
                bg=Theme.BG_SECONDARY, fg=Theme.ACCENT_GREEN,
                font=("Consolas", 11, "bold")).pack(anchor="w", padx=10, pady=(20, 5))

        self.stats_labels = {}
        for label in ["Génération", "Meilleur Fitness", "Fitness Moyen", "Diversité", "Meilleur ADN"]:
            frame = tk.Frame(control_frame, bg=Theme.BG_SECONDARY)
            frame.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(frame, text=f"{label}:", bg=Theme.BG_SECONDARY,
                    fg=Theme.TEXT_MUTED, font=("Consolas", 9), width=18, anchor="w"
                    ).pack(side=tk.LEFT)
            val = tk.Label(frame, text="—", bg=Theme.BG_SECONDARY,
                          fg=Theme.TEXT_PRIMARY, font=("Consolas", 9, "bold"))
            val.pack(side=tk.LEFT)
            self.stats_labels[label] = val

        self.evolution_plot = EvolutionPlot(self.tab_evolution)

    def _build_param_slider(self, parent, label, min_val, max_val, default, attr_name, scale=1):
        frame = tk.Frame(parent, bg=Theme.BG_SECONDARY)
        frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(frame, text=f"{label}:", bg=Theme.BG_SECONDARY,
                fg=Theme.TEXT_SECONDARY, font=("Consolas", 9), width=18, anchor="w"
                ).pack(side=tk.LEFT)

        var = tk.IntVar(value=default)
        slider = tk.Scale(frame, from_=min_val, to=max_val, orient=tk.HORIZONTAL,
                         variable=var, bg=Theme.BG_SECONDARY, fg=Theme.TEXT_SECONDARY,
                         highlightthickness=0, troughcolor=Theme.BG_TERTIARY,
                         activebackground=Theme.ACCENT_CYAN, showvalue=False,
                         length=120)
        slider.pack(side=tk.LEFT)

        val_label = tk.Label(frame, text=str(default), bg=Theme.BG_SECONDARY,
                            fg=Theme.ACCENT_CYAN, font=("Consolas", 9), width=4)
        val_label.pack(side=tk.LEFT)

        def update(val):
            val_label.config(text=str(int(float(val))))
            setattr(self.engine, attr_name, int(float(val)) * scale if scale != 1 else int(float(val)))

        slider.config(command=update)

    def _build_proteins_tab(self):
        self.protein_graph = ProteinGraph(self.tab_proteins, self.config)

    def _build_phylo_tab(self):
        self.phylo_plot = PhylogenyPlot(self.tab_phylo)

    def _build_epigenetic_tab(self):
        self.epi_heatmap = EpigeneticHeatmap(self.tab_epi, self.config)

    def _build_plasmids_tab(self):
        self.plasmid_view = PlasmidView(self.tab_plasmids, self.config)

    def _build_editor_tab(self):
        self.dna_editor = DNAEditor(self.tab_editor)
        self.dna_editor.current_lang = self.engine.target_lang

    def _build_operons_tab(self):
        self.operon_panel = OperonPanel(self.tab_operons, self.config)

    def _build_console_tab(self):
        self.console = ConsoleWidget(self.tab_console)

    def _build_statusbar(self):
        self.statusbar = tk.Label(self.root, text="Prêt | Bio-Compiler Studio v4.0 — Multi-Langages",
                                 bg=Theme.BG_SECONDARY, fg=Theme.TEXT_MUTED,
                                 font=("Consolas", 9), anchor="w", padx=10)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)

    # ── Actions ──

    def _change_language(self, lang: str):
        """Change le langage cible pour la génération de protéines et la transcription."""
        if lang not in Theme.SUPPORTED_LANGUAGES:
            return
        self.engine.set_target_language(lang)
        self.lang_var.set(lang)
        if hasattr(self, 'dna_editor'):
            self.dna_editor.current_lang = lang
        logger.success(f"Langage changé: {lang}")
        self.statusbar.config(text=f"Langue: {lang.upper()} | Prêt")

    def _start_evolution(self):
        kws = self.keywords_entry.get().strip().split()
        if kws:
            self.engine.target_keywords = kws
        self.engine.start_evolution()
        self.status_label.config(text="▶️ En cours...", fg=Theme.ACCENT_GREEN)

    def _pause_evolution(self):
        self.engine.pause_evolution()
        status = "⏸️ En pause" if self.engine.is_paused else "▶️ En cours..."
        self.status_label.config(text=status, 
                                fg=Theme.ACCENT_AMBER if self.engine.is_paused else Theme.ACCENT_GREEN)

    def _stop_evolution(self):
        self.engine.stop_evolution()
        self.status_label.config(text="⏹️ Arrêté", fg=Theme.ACCENT_RED)

    def _generate_proteins(self):
        """Génère les fichiers protéines dans le langage actuel."""
        if not ProtEngine:
            messagebox.showwarning("Génération", "Générateur de protéines non disponible.\n"
                                              "Vérifiez que prot_generator_multilang.py est accessible.")
            return
        output_dir = filedialog.askdirectory(title="Dossier de sortie pour les protéines",
                                             initialdir="./slot")
        if not output_dir:
            output_dir = f"./slot_{self.engine.target_lang}"
        
        def generate():
            self.engine.generate_proteins(output_dir, self.engine.target_lang)
        
        threading.Thread(target=generate, daemon=True).start()
        logger.info(f"Génération des protéines lancée vers {output_dir} ({self.engine.target_lang})")

    def _random_dna(self):
        self.dna_editor._random_dna()
        self.notebook.select(self.tab_editor)

    def _load_config(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            try:
                self.config = json.loads(Path(path).read_text())
                self.engine = BioCompilerEngine(path, target_lang=self.engine.target_lang)
                self.engine.add_observer(self._on_engine_event)
                # Rafraîchir les vues
                if hasattr(self, 'protein_graph'):
                    self.protein_graph.config = self.config
                    self.protein_graph._build_graph()
                if hasattr(self, 'epi_heatmap'):
                    self.epi_heatmap.config = self.config
                    self.epi_heatmap._draw_heatmap()
                if hasattr(self, 'plasmid_view'):
                    self.plasmid_view.config = self.config
                    self.plasmid_view._draw_plasmids()
                if hasattr(self, 'operon_panel'):
                    self.operon_panel.operons = self.config.get("operons", [])
                    # Rebuild operon panel
                    for widget in self.tab_operons.winfo_children():
                        widget.destroy()
                    self._build_operons_tab()
                logger.success(f"Configuration chargée: {path}")
                messagebox.showinfo("Configuration", f"Configuration chargée:\n{path}")
            except Exception as e:
                logger.error(f"Erreur chargement config: {e}")
                messagebox.showerror("Erreur", f"Impossible de charger la configuration:\n{e}")

    def _save_config(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                           filetypes=[("JSON", "*.json")])
        if path:
            with open(path, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.success(f"Configuration sauvegardée: {path}")

    def _show_params(self):
        messagebox.showinfo("Paramètres", 
                           f"Générations: {self.engine.max_generations}\n"
                           f"Population: {self.engine.population_size}\n"
                           f"Mutation: {self.engine.mutation_rate}\n"
                           f"Indel: {self.engine.indel_rate}\n"
                           f"Nic: {self.engine.niche_count}\n"
                           f"Coévolution: {self.engine.coevolve}\n"
                           f"Langage: {self.engine.target_lang}")

    def _export_fitness(self):
        if not self.engine.fitness_history:
            messagebox.showwarning("Export", "Aucune donnée d'évolution à exporter")
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                           filetypes=[("PNG", "*.png"), ("SVG", "*.svg")])
        if path and self.evolution_plot.canvas:
            self.evolution_plot.fig.savefig(path, dpi=150, bbox_inches="tight",
                                           facecolor=Theme.BG_PRIMARY)
            logger.success(f"Graphique exporté: {path}")

    def _export_newick(self):
        if not self.engine.phylogeny:
            messagebox.showwarning("Export", "Aucune phylogénie à exporter")
            return
        path = filedialog.asksaveasfilename(defaultextension=".nwk",
                                           filetypes=[("Newick", "*.nwk")])
        if path:
            newick = self._build_newick(self.engine.phylogeny)
            with open(path, "w") as f:
                f.write(newick + ";\n")
            logger.success(f"Phylogénie exportée: {path}")

    def _build_newick(self, phylogeny):
        if not phylogeny:
            return "()"
        by_gen = defaultdict(list)
        for node in phylogeny:
            by_gen[node["generation"]].append(node)

        def build(gen):
            nodes = by_gen.get(gen, [])
            if not nodes:
                return ""
            labels = [f"{n['node_id']}:{n['fitness']:.3f}" for n in nodes]
            return "(" + ",".join(labels) + ")"

        result = ""
        for gen in sorted(by_gen.keys()):
            if result:
                result = f"({result},{build(gen)})"
            else:
                result = build(gen)
        return result or "()"

    def _export_fasta(self):
        if not self.engine.best_dna:
            messagebox.showwarning("Export", "Aucune séquence à exporter")
            return
        path = filedialog.asksaveasfilename(defaultextension=".fasta",
                                           filetypes=[("FASTA", "*.fasta")])
        if path:
            with open(path, "w") as f:
                f.write(f">BioCompiler_Best_Gen{self.engine.current_generation}_{self.engine.target_lang}\n")
                f.write(self.engine.best_dna + "\n")
            logger.success(f"Séquence exportée: {path}")

    def _export_code(self):
        if not self.engine.best_dna:
            messagebox.showwarning("Export", "Aucun code à exporter")
            return
        ext_map = {"python": ".py", "csharp": ".cs", "javascript": ".js", "rust": ".rs", "go": ".go"}
        ext = ext_map.get(self.engine.target_lang, ".txt")
        path = filedialog.asksaveasfilename(defaultextension=ext,
                                           filetypes=[(self.engine.target_lang.upper(), f"*{ext}")])
        if path:
            code = self.engine.transcribe_dna(self.engine.best_dna)
            with open(path, "w") as f:
                f.write(code)
            logger.success(f"Code exporté: {path} ({self.engine.target_lang})")

    def _show_docs(self):
        docs = """Bio-Compiler Studio v4.0 — Multi-Langages

🧬 Évolution Génétique:
  • Lancez l'évolution via le bouton Start
  • Ajustez les paramètres en temps réel
  • Visualisez la convergence sur le graphique

🌐 Multi-Langages (NOUVEAU !):
  • Python, C#, JavaScript, Rust, Go
  • Changez la langue cible via le menu ou la toolbar
  • La génération de protéines s'adapte automatiquement

🔬 Protéines:
  • Graphe des dépendances et héritages
  • Coloration par phase cellulaire

🌳 Phylogénie:
  • Dendrogramme de l'évolution
  • Coloration par fitness

🧪 Épigénétique:
  • Heatmap des marqueurs H3K4me3, H3K27me3...

🧫 Plasmides:
  • Vue circulaire des structures

✏️ Éditeur ADN:
  • Coloration syntaxique des codons
  • Transcription temps réel

🎛️ Opérons:
  • État des promoteurs en temps réel
"""
        messagebox.showinfo("Documentation", docs)

    def _show_about(self):
        messagebox.showinfo("À propos",
                           "🧬 Bio-Compiler Studio v4.0\n"
                           "Interface graphique pour Bio-Compiler_evolved\n\n"
                           "NOUVEAUTÉS v4.0 :\n"
                           "• Support de 5 langages (Python, C#, JS, Rust, Go)\n"
                           "• Génération de protéines multi-langages\n\n"
                           "Inspirations: Hofstadter, Conway, Varela & Maturana\n"
                           "Thème: Laboratoire de biologie moléculaire")

    # ── Événements ──

    def _on_engine_event(self, event_type, data):
        if event_type == "generation":
            self.root.after(0, lambda: self._update_stats(data))
        elif event_type == "finished":
            self.root.after(0, lambda: self._on_evolution_finished(data))

    def _update_stats(self, data):
        self.stats_labels["Génération"].config(text=str(data["generation"]))
        self.stats_labels["Meilleur Fitness"].config(text=f"{data['best_fitness']:.4f}")
        self.stats_labels["Fitness Moyen"].config(text=f"{data['avg_fitness']:.4f}")
        self.stats_labels["Diversité"].config(text=f"{data.get('diversity', 0):.3f}")

        dna_preview = data.get("best_dna", "")[:30] + "..." if len(data.get("best_dna", "")) > 30 else data.get("best_dna", "")
        self.stats_labels["Meilleur ADN"].config(text=dna_preview)

        progress = (data["generation"] + 1) / self.engine.max_generations * 100
        self.progress.config(value=progress)

        self.evolution_plot.update(self.engine.fitness_history)

        if hasattr(self, 'operon_panel'):
            cellular_state = int(data["best_fitness"] * 10) % 12
            self.operon_panel.update_state(cellular_state, data["generation"])

    def _on_evolution_finished(self, data):
        self.status_label.config(text="✅ Terminé", fg=Theme.ACCENT_GREEN)
        self.progress.config(value=100)

        if hasattr(self, 'phylo_plot'):
            self.phylo_plot.update(self.engine.phylogeny)

        if hasattr(self, 'dna_editor') and self.engine.best_dna:
            self.dna_editor.set_dna(self.engine.best_dna)

        logger.success("Évolution terminée — données mises à jour")

    def _on_log(self, timestamp, level, message):
        if hasattr(self, 'console') and hasattr(self, 'root') and self.root:
            try:
                self.root.after(0, lambda ts=timestamp, lv=level, msg=message: 
                    self.console.append(ts, lv, msg))
            except Exception:
                pass

    def _schedule_refresh(self):
        self.root.after(self._refresh_interval, self._schedule_refresh)

    def run(self):
        self.root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE CLI + GUI
# ══════════════════════════════════════════════════════════════════════════════

def run_cli(args):
    """Mode ligne de commande — interface originale Bio-Compiler."""
    print("🧬 Bio-Compiler Studio v4.0 — Mode CLI Multi-Langages")
    print("━" * 60)

    if not BioCompiler:
        print("❌ Erreur: Bio-Compiler_evolved.py non disponible")
        return 1

    config_path = args.config or str(UPLOAD_DIR / "proteome_config_949.json")
    target_lang = args.lang or "python"

    if args.generate_proteins:
        print(f"🧬 Génération des protéines ({target_lang})...")
        if ProtEngine:
            try:
                engine = ProtEngine.ProtEngine(config_path, args.output or "./slot",
                                              generation=0, target_lang=target_lang)
                engine.generate_all()
            except Exception as e:
                print(f"❌ Erreur génération: {e}")
                return 1
        else:
            print("❌ Générateur de protéines non disponible")
            return 1

    if args.evolve:
        print(f"🧬 Évolution génétique en cours...")
        print(f"   Générations: {args.gens}")
        print(f"   Population: {args.pop}")
        print(f"   Mutation: {args.mut_rate}")
        print(f"   Langage: {target_lang}")

        loader = BioCompiler.ProteinLoader(args.slot or "./slot")
        genetic_code = BioCompiler.load_genetic_code(args.ext_codons)

        engine = BioCompiler.DNAEvolutionEngine(
            target_keywords=args.target_kw or ["for", "if", "try", "print"],
            pop_size=args.pop or 30,
            gens=args.gens or 50,
            mut_rate=args.mut_rate or 0.02,
            indel_rate=args.indel_rate or 0.005,
            lang=target_lang,
            loader=loader,
            genetic_code=genetic_code,
            niche_count=args.niches or 3,
            coevolve=args.coevolve,
        )

        best_dna = engine.evolve()
        print(f"\n🏆 Meilleure séquence: {best_dna}")
        print(f"   Longueur: {len(best_dna)} bp")

        if args.output:
            transcriptor = BioCompiler.DNAToCodeTranscriptor(target_lang, loader, genetic_code)
            code = transcriptor.transcribe(best_dna)
            with open(args.output, "w") as f:
                f.write(code)
            print(f"   Code exporté: {args.output} ({target_lang})")

        if args.export_newick:
            engine.export_newick("phylogeny.nwk")

        if args.export_history:
            engine.export_history("evolution_history.json")

    if args.dna:
        print(f"🧪 Transcription de la séquence ADN vers {target_lang}...")
        loader = BioCompiler.ProteinLoader(args.slot or "./slot")
        genetic_code = BioCompiler.load_genetic_code(args.ext_codons)
        transcriptor = BioCompiler.DNAToCodeTranscriptor(target_lang, loader, genetic_code)
        code = transcriptor.transcribe(args.dna.upper())

        if args.output:
            with open(args.output, "w") as f:
                f.write(code)
            print(f"✅ Code généré: {args.output}")
        else:
            print("\n" + "━" * 60)
            print(code)
            print("━" * 60)

    if args.export_fasta and args.dna:
        fasta = f">BioCode_{target_lang}\n{args.dna.upper()}\n"
        with open("sequence.fasta", "w") as f:
            f.write(fasta)
        print("🧬 FASTA exporté: sequence.fasta")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="🧬 Bio-Compiler Studio v4.0 — GUI & CLI Multi-Langages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Mode GUI (par défaut)
  python bio_compiler_studio_v4.py

  # Mode CLI — Évolution vers Rust
  python bio_compiler_studio_v4.py --cli --evolve --gens 100 --pop 50 --lang rust

  # Mode CLI — Générer protéines en Go
  python bio_compiler_studio_v4.py --cli --generate-proteins --lang go

  # Mode CLI — Transcription manuelle
  python bio_compiler_studio_v4.py --cli --dna ATGTTTCTGCTC... --lang javascript
        """)

    parser.add_argument("--cli", action="store_true",
                       help="Mode ligne de commande")
    parser.add_argument("--gui", action="store_true",
                       help="Mode interface graphique (par défaut)")

    parser.add_argument("--config", help="Chemin vers le JSON de configuration")
    parser.add_argument("--dna", help="Séquence ADN manuelle")
    parser.add_argument("--lang", choices=["python", "csharp", "javascript", "rust", "go"],
                       default="python", help="Langage cible")
    parser.add_argument("--slot", default="./slot", help="Dossier des fichiers .prot")
    parser.add_argument("--output", "-o", help="Fichier de sortie")

    parser.add_argument("--evolve", action="store_true", help="Activer l'algorithme génétique")
    parser.add_argument("--generate-proteins", action="store_true", help="Générer les .prot")
    parser.add_argument("--target-kw", nargs="+", default=["for", "if", "try", "print"])
    parser.add_argument("--gens", type=int, default=50)
    parser.add_argument("--pop", type=int, default=30)
    parser.add_argument("--mut-rate", type=float, default=0.02)
    parser.add_argument("--indel-rate", type=float, default=0.005)
    parser.add_argument("--niches", type=int, default=3)
    parser.add_argument("--coevolve", action="store_true")
    parser.add_argument("--ext-codons", help="JSON externe pour étendre la table génétique")

    parser.add_argument("--export-fasta", action="store_true")
    parser.add_argument("--export-newick", action="store_true")
    parser.add_argument("--export-history", action="store_true")

    args = parser.parse_args()

    if args.cli:
        return run_cli(args)
    else:
        app = BioCompilerStudio(args.config)
        app.run()
        return 0


if __name__ == "__main__":
    sys.exit(main())
