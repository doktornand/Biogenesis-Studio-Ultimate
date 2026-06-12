#!/usr/bin/env python3
"""
Bio-Compiler_evolved.py — Transcripteur ADN v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Nouvelles capacités :
  • Table génétique extensible via JSON externe
  • Codons épigénétiques (méthylation → silençage de blocs suivants)
  • Opérons : groupes de codons co-régulés par un promoteur
  • Transposons : codons qui sautent et réordonnent la séquence
  • Mutations structurales : indels (insertion/délétion de codons entiers)
  • Fitness sémantique via AST Python (complexité cyclomatique, profondeur)
  • Fitness entropique (diversité de la population → anti-convergence prématurée)
  • Coévolution hôte/parasite (deux populations qui s'évaluent mutuellement)
  • Niche partitioning (partitionnement de l'espace de fitness)
  • Recombinaison homologue alignée sur les ORF
  • Export Newick de la phylogénie évolutive
  • Profils de langage extensibles (Rust, Go ajoutés)
"""
import os, sys, re, random, argparse, hashlib, ast, json, math
from pathlib import Path
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from collections import defaultdict

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    # Fallback si colorama n'est pas installé
    class Fore:
        RED = ''; GREEN = ''; YELLOW = ''; CYAN = ''; MAGENTA = '';
        LIGHTBLUE_EX = ''; RESET_ALL = ''
    class Style:
        RESET_ALL = ''

# ══════════════════════════════════════════════════════════════════════
# PROFILS DE LANGAGE (extensibles)
# ══════════════════════════════════════════════════════════════════════
LANG_PROFILES: Dict[str, Dict] = {
    "python": {
        "ext": ".py", "comment": "#", "state": "self.state",
        "organelles": "self.organelles",
        "imports": "import random\nimport math\n",
        "class_def": "class BioProgram:", "init": "def __init__(self):",
        "exec": "def execute(self):",
        "loop_for": "for _ in range(self.state % 5 + 1):",
        "loop_while": "while self.state > 0:",
        "cond_if": "if self.state % 2 == 0:",
        "cond_elif": "elif self.state > 10:",
        "try_block": "try:", "catch_block": "except Exception as e:",
        "var_int":   "gene_{pos} = random.randint(0, 100)",
        "var_str":   "gene_{pos} = f'val_{pos}'",
        "var_bool":  "gene_{pos} = self.state % 2 == 0",
        "var_float": "gene_{pos} = random.random() * self.state",
        "state_inc": "self.state += 1",
        "state_dec": "self.state = max(0, self.state - 1)",
        "print": "print", "indent": "    ",
    },
    "csharp": {
        "ext": ".cs", "comment": "//", "state": "_state",
        "organelles": "_organelles",
        "imports": "using System;\nusing System.Collections.Generic;\n",
        "class_def": "public class BioProgram {",          # AJOUT DE {
        "init": "public BioProgram() {",                   # AJOUT DE {
        "exec": "public void Execute() {",                 # AJOUT DE {
        "loop_for": "for (int i = 0; i < _state % 5 + 1; i++) {", # AJOUT DE {
        "loop_while": "while (_state > 0) {",              # AJOUT DE {
        "cond_if": "if (_state % 2 == 0) {",               # AJOUT DE {
        "cond_elif": "} else if (_state > 10) {",          # AJOUT DE } et {
        "try_block": "try {", 
        "catch_block": "} catch (Exception e) {",          # AJOUT DE }
        "var_int":   "int gene_{pos} = new Random().Next(0, 100);",
        "var_str":   "string gene_{pos} = $\"val_{pos}\";",
        "var_bool":  "bool gene_{pos} = _state % 2 == 0;",
        "var_float": "double gene_{pos} = new Random().NextDouble() * _state;",
        "state_inc": "_state++;", 
        "state_dec": "_state = Math.Max(0, _state - 1);",
        "print": "Console.WriteLine", 
        "indent": "    ",
    },
    "javascript": {
        "ext": ".js", "comment": "//", "state": "this.state",
        "organelles": "this.organelles",
        "imports": "// Standard JS\n",
        "class_def": "class BioProgram", "init": "constructor()",
        "exec": "execute()",
        "loop_for": "for (let i = 0; i < (this.state % 5 + 1); i++)",
        "loop_while": "while (this.state > 0)",
        "cond_if": "if (this.state % 2 === 0)",
        "cond_elif": "else if (this.state > 10)",
        "try_block": "try {", "catch_block": "catch (e) {",
        "var_int":   "let gene_{pos} = Math.floor(Math.random() * 100);",
        "var_str":   "let gene_{pos} = `val_${pos}`;",
        "var_bool":  "let gene_{pos} = this.state % 2 === 0;",
        "var_float": "let gene_{pos} = Math.random() * this.state;",
        "state_inc": "this.state++;",
        "state_dec": "this.state = Math.max(0, this.state - 1);",
        "print": "console.log", "indent": "  ",
    },
    "rust": {
        "ext": ".rs", "comment": "//", "state": "self.state",
        "organelles": "self.organelles",
        "imports": "use rand::Rng;\n",
        "class_def": "pub struct BioProgram { state: i32, organelles: Vec<String> }",
        "init": "pub fn new() -> Self",
        "exec": "pub fn execute(&mut self)",
        "loop_for": "for _ in 0..(self.state % 5 + 1) {",
        "loop_while": "while self.state > 0 {",
        "cond_if": "if self.state % 2 == 0 {",
        "cond_elif": "} else if self.state > 10 {",
        "try_block": "// try (Rust uses Result):",
        "catch_block": "// catch:",
        "var_int":   "let gene_{pos}: i32 = rand::thread_rng().gen_range(0..100);",
        "var_str":   "let gene_{pos} = format!(\"val_{pos}\");",
        "var_bool":  "let gene_{pos}: bool = self.state % 2 == 0;",
        "var_float": "let gene_{pos}: f64 = rand::thread_rng().gen::<f64>() * self.state as f64;",
        "state_inc": "self.state += 1;",
        "state_dec": "self.state = (self.state - 1).max(0);",
        "print": "println!", "indent": "    ",
    },
    "go": {
        "ext": ".go", "comment": "//", "state": "b.state",
        "organelles": "b.organelles",
        "imports": "import (\n    \"fmt\"\n    \"math/rand\"\n)\n",
        "class_def": "type BioProgram struct { state int; organelles []string }",
        "init": "func NewBioProgram() *BioProgram",
        "exec": "func (b *BioProgram) Execute()",
        "loop_for": "for i := 0; i < b.state%5+1; i++ {",
        "loop_while": "for b.state > 0 {",
        "cond_if": "if b.state%2 == 0 {",
        "cond_elif": "} else if b.state > 10 {",
        "try_block": "// Go error handling:",
        "catch_block": "if err != nil {",
        "var_int":   "gene{pos} := rand.Intn(100)",
        "var_str":   "gene{pos} := fmt.Sprintf(\"val_%d\", {pos})",
        "var_bool":  "gene{pos} := b.state%2 == 0",
        "var_float": "gene{pos} := rand.Float64() * float64(b.state)",
        "state_inc": "b.state++",
        "state_dec": "if b.state > 0 { b.state-- }",
        "print": "fmt.Println", "indent": "\t",
    },
}

# ══════════════════════════════════════════════════════════════════════
# TABLE GÉNÉTIQUE ÉTENDUE
# ══════════════════════════════════════════════════════════════════════
class ActionType(Enum):
    FUNCTION_CALL    = auto()
    BEGIN_LOOP       = auto()
    BEGIN_CONDITION  = auto()
    BEGIN_TRY        = auto()
    END_BLOCK        = auto()
    CREATE_VAR       = auto()
    MODIFY_STATE     = auto()
    EPIGENETIC_MARK  = auto()
    TRANSPOSON       = auto()
    OPERON_START     = auto()
    OPERON_END       = auto()
    COMMENT_BLOCK    = auto()
    NOOP             = auto()

_BASE_GENETIC_CODE: Dict[str, Tuple] = {
    "ATG": (ActionType.FUNCTION_CALL,   "initialize.prot"),
    "TTT": (ActionType.FUNCTION_CALL,   "phenylalanine.prot"),
    "CTC": (ActionType.FUNCTION_CALL,   "process_data.prot"),
    "CTG": (ActionType.FUNCTION_CALL,   "analyze.prot"),
    "GCA": (ActionType.FUNCTION_CALL,   "heatshock.prot"),
    "GCT": (ActionType.FUNCTION_CALL,   "repair.prot"),
    "TCT": (ActionType.BEGIN_LOOP,      "for"),
    "TCC": (ActionType.BEGIN_LOOP,      "while"),
    "TCG": (ActionType.BEGIN_CONDITION, "if"),
    "CCT": (ActionType.BEGIN_CONDITION, "elif"),
    "CCC": (ActionType.BEGIN_TRY,),
    "TGA": (ActionType.END_BLOCK,),
    "TAA": (ActionType.END_BLOCK,),
    "TAG": (ActionType.END_BLOCK,),
    "TAT": (ActionType.CREATE_VAR,      "int"),
    "TAC": (ActionType.CREATE_VAR,      "str"),
    "CAT": (ActionType.CREATE_VAR,      "bool"),
    "CAC": (ActionType.CREATE_VAR,      "float"),
    "GGG": (ActionType.MODIFY_STATE,    "inc"),
    "GGA": (ActionType.MODIFY_STATE,    "dec"),
    "AAA": (ActionType.NOOP,),
    "AAT": (ActionType.NOOP,),
    "CGG": (ActionType.EPIGENETIC_MARK, 2),
    "CGC": (ActionType.EPIGENETIC_MARK, 4),
    "TTA": (ActionType.TRANSPOSON,      3),
    "TTG": (ActionType.TRANSPOSON,      -2),
    "GAT": (ActionType.OPERON_START,    "OP_A"),
    "GAC": (ActionType.OPERON_END,),
    "GTC": (ActionType.COMMENT_BLOCK,   "philosophique"),
}

PHILOSOPHICAL_COMMENTS = [
    "// Ce code ne sait pas qu'il s'exécute. Ou le sait-il ?",
    "// La récursion est le miroir que le programme tend à lui-meme.",
    "// Chaque état est une mémoire. Chaque mémoire est un état futur.",
    "// Je suis la somme de mes mutations accumulées.",
    "// L'entropie croît. Le programme résiste. Pour l'instant.",
    "// La boucle se ferme. Mais sur quoi ?",
    "// Un codon silencieux n'est pas un codon inutile.",
    "// L'émergence n'est pas prévue. Elle est inévitable.",
]

def load_genetic_code(ext_path: Optional[str] = None) -> Dict[str, Tuple]:
    code = dict(_BASE_GENETIC_CODE)
    if ext_path and Path(ext_path).exists():
        ext = json.loads(Path(ext_path).read_text())
        for codon, action_list in ext.items():
            act_type = ActionType[action_list[0]]
            code[codon.upper()] = tuple([act_type] + action_list[1:])
        print(f"  Table genetique etendue : +{len(ext)} codons depuis {ext_path}")
    return code

# ══════════════════════════════════════════════════════════════════════
# CHARGEUR DE PROTEINES
# ══════════════════════════════════════════════════════════════════════
class ProteinLoader:
    def __init__(self, slot_dir: str):
        self.slot_dir = Path(slot_dir)
        self.cache: Dict[str, str] = {}
        self.slot_dir.mkdir(parents=True, exist_ok=True)

    def load(self, protein_name: str) -> Optional[str]:
        if protein_name in self.cache:
            return self.cache[protein_name]
        path = self.slot_dir / protein_name
        if path.exists():
            content = path.read_text(encoding="utf-8")
            self.cache[protein_name] = content
            return content
        return None

# ══════════════════════════════════════════════════════════════════════
# TRANSCRIPTEUR MULTI-LANGAGES
# ══════════════════════════════════════════════════════════════════════
class DNAToCodeTranscriptor:
    def __init__(self, lang: str, loader: ProteinLoader,
                 genetic_code: Optional[Dict] = None):
        self.lang = lang.lower()
        if self.lang not in LANG_PROFILES:
            raise ValueError(f"Langage inconnu: {self.lang}. Disponibles: {list(LANG_PROFILES)}")
        self.profile = LANG_PROFILES[self.lang]
        self.loader = loader
        self.genetic_code = genetic_code or _BASE_GENETIC_CODE
        self.code: List[str] = []
        self.stack: List[ActionType] = []
        self.indent: int = 0

    def transcribe(self, dna: str) -> str:
        self.code.clear()
        self.stack.clear()
        self.indent = 0
        self._line(self.profile["imports"])
        self._line(self.profile["class_def"])
        self._push()
        self._line(self.profile["init"])
        self._push()
        self._line(f"{self.profile['state']} = 0")
        self._line(f"{self.profile['organelles']} = []")
        self._pop()
        self._pop()
        self._line(self.profile["exec"])
        self._push()

        codons = [dna[i:i+3].upper() for i in range(0, len(dna)-2, 3)]
        codons = self._apply_transposons(codons)

        methyl_count = 0
        operon_active = False
        operon_condition_met = True

        for pos, codon in enumerate(codons):
            if methyl_count > 0:
                self._line(f"{self.profile['comment']} [METHYLE] Codon {codon} silence epigenetiquement")
                methyl_count -= 1
                continue

            action = self.genetic_code.get(codon)
            if not action:
                self._line(f"{self.profile['comment']} Mutation silencieuse: {codon}")
                continue

            act_type, *meta = action

            if act_type == ActionType.OPERON_START:
                operon_active = True
                self._line(f"{self.profile['comment']} [OPERON:{meta[0]}] Debut co-regulation")
                continue
            if act_type == ActionType.OPERON_END:
                operon_active = False
                self._line(f"{self.profile['comment']} [OPERON] Fin co-regulation")
                continue
            if operon_active and not operon_condition_met:
                self._line(f"{self.profile['comment']} [OPERON] Codon {codon} supprime")
                continue

            if act_type == ActionType.FUNCTION_CALL:
                prot = self.loader.load(meta[0])
                if prot:
                    for line in prot.splitlines():
                        self._line(line.strip())
                else:
                    self._line(f"{self.profile['print']}(\"Proteine {meta[0]} manquante\")")

            elif act_type == ActionType.BEGIN_LOOP:
                self._line(self.profile[f"loop_{meta[0]}"])
                self._push()

            elif act_type == ActionType.BEGIN_CONDITION:
                self._line(self.profile[f"cond_{meta[0]}"])
                self._push()

            elif act_type == ActionType.BEGIN_TRY:
                self._line(self.profile["try_block"])
                self._push()

            elif act_type == ActionType.END_BLOCK:
                self._close_block()

            elif act_type == ActionType.CREATE_VAR:
                self._line(self.profile[f"var_{meta[0]}"].format(pos=pos))
                self._line(f"{self.profile['organelles']}.append(gene_{pos})")

            elif act_type == ActionType.MODIFY_STATE:
                if meta[0] == "inc":
                    self._line(self.profile["state_inc"])
                else:
                    self._line(self.profile["state_dec"])

            elif act_type == ActionType.EPIGENETIC_MARK:
                methyl_count = meta[0]
                self._line(f"{self.profile['comment']} [EPIGENETIQUE] Methylation: {methyl_count} codons silences")

            elif act_type == ActionType.COMMENT_BLOCK:
                self._line(random.choice(PHILOSOPHICAL_COMMENTS))

            elif act_type == ActionType.NOOP:
                self._line(f"{self.profile['comment']} Intron (non-codant)")

        while self.stack:
            self._close_block()
        self._pop()
        self._pop()
        return "\n".join(self.code)

    def _apply_transposons(self, codons: List[str]) -> List[str]:
        result = list(codons)
        i = 0
        while i < len(result):
            action = self.genetic_code.get(result[i])
            if action and action[0] == ActionType.TRANSPOSON:
                delta = action[1]
                target = min(max(0, i + delta), len(result) - 1)
                codon = result.pop(i)
                result.insert(target, codon)
                if i < len(result):
                    result[i] = "AAA"
            i += 1
        return result

    def _close_block(self):
        if self.stack:
            top = self.stack.pop()
            self._pop()
            if top == ActionType.BEGIN_TRY:
                self._line(self.profile["catch_block"])
                self._push()
                self._line("}")
                self._pop()
            else:
                self._line("}")  # Ajoute systématiquement l'accolade fermante

    def _push(self):
        self.stack.append(ActionType.BEGIN_LOOP)
        self.indent += 1

    def _pop(self):
        self.indent = max(0, self.indent - 1)
        if self.stack:
            self.stack.pop()

    def _line(self, txt: str):
        if not txt:
            self.code.append("")
            return
        self.code.append(f"{self.profile['indent'] * self.indent}{txt}")


# ══════════════════════════════════════════════════════════════════════
# FITNESS SEMANTIQUE
# ══════════════════════════════════════════════════════════════════════
class SemanticFitnessEvaluator:
    def __init__(self, target_keywords: List[str], lang: str):
        self.target_kw = target_keywords
        self.lang = lang

    def evaluate(self, code: str) -> float:
        score = 0.0
        for kw in self.target_kw:
            if kw.lower() in code.lower():
                score += 2.0

        if self.lang == "python":
            score += self._python_ast_score(code)
        else:
            score += self._heuristic_score(code)

        score += self._structural_balance(code)
        return score

    def _python_ast_score(self, code: str) -> float:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return -2.0

        score = 0.0
        branches = sum(1 for node in ast.walk(tree)
                       if isinstance(node, (ast.If, ast.For, ast.While,
                                            ast.ExceptHandler, ast.With)))
        score += min(branches * 0.5, 4.0)

        depth = self._ast_depth(tree)
        score += min(depth * 0.3, 3.0)

        classes = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        functions = sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))
        score += classes * 1.5 + functions * 0.8

        return score

    def _ast_depth(self, node: ast.AST, depth: int = 0) -> int:
        children = list(ast.iter_child_nodes(node))
        if not children:
            return depth
        return max(self._ast_depth(c, depth + 1) for c in children)

    def _heuristic_score(self, code: str) -> float:
        score = 0.0
        patterns = [r'\bfor\b', r'\bwhile\b', r'\bif\b', r'\btry\b',
                    r'\bclass\b', r'\bdef\b', r'\bfunction\b']
        for pattern in patterns:
            score += len(re.findall(pattern, code)) * 0.4
        return min(score, 6.0)

    def _structural_balance(self, code: str) -> float:
        opens = code.count("{") + code.count("(") + code.count("[")
        closes = code.count("}") + code.count(")") + code.count("]")
        return max(0, 5.0 - abs(opens - closes) * 0.5)


# ══════════════════════════════════════════════════════════════════════
# NOEUD PHYLOGENETIQUE
# ══════════════════════════════════════════════════════════════════════
@dataclass
class PhyloNode:
    dna: str
    fitness: float
    generation: int
    parent_id: Optional[str] = None
    node_id: str = field(default_factory=lambda: hashlib.md5(
        random.randbytes(8)).hexdigest()[:8])
    children: List["PhyloNode"] = field(default_factory=list)

    def to_newick(self) -> str:
        if not self.children:
            return f"{self.node_id}:{self.fitness:.3f}"
        inner = ",".join(c.to_newick() for c in self.children)
        return f"({inner}){self.node_id}:{self.fitness:.3f}"


# ══════════════════════════════════════════════════════════════════════
# MOTEUR D'EVOLUTION
# ══════════════════════════════════════════════════════════════════════
class DNAEvolutionEngine:
    def __init__(self,
                 target_keywords: List[str],
                 pop_size:  int   = 30,
                 gens:      int   = 50,
                 mut_rate:  float = 0.02,
                 indel_rate: float= 0.005,
                 lang:      str   = "python",
                 loader:    Optional[ProteinLoader] = None,
                 genetic_code: Optional[Dict] = None,
                 niche_count: int = 3,
                 coevolve:  bool  = False):

        self.target_kw   = target_keywords
        self.pop_size    = pop_size
        self.gens        = gens
        self.mut_rate    = mut_rate
        self.indel_rate  = indel_rate
        self.bases       = "ATCG"
        self.codon_len   = 3
        self.genome_len  = 45
        self.lang        = lang
        self.niche_count = niche_count
        self.coevolve    = coevolve

        self.genetic_code = genetic_code or _BASE_GENETIC_CODE
        _loader = loader or ProteinLoader("./slot")
        self.transcriptor = DNAToCodeTranscriptor(lang, _loader, self.genetic_code)
        self.fitness_eval = SemanticFitnessEvaluator(target_keywords, lang)

        self.pop = [self._rand() for _ in range(pop_size)]
        self.parasite_pop = [self._rand() for _ in range(pop_size // 2)] if coevolve else []

        self.phylo_roots: List[PhyloNode] = []
        self.phylo_nodes: Dict[str, PhyloNode] = {}
        self.history: List[Dict] = []

    def _rand(self) -> str:
        length = random.randint(self.genome_len - 6, self.genome_len + 6)
        length = (length // 3) * 3
        return "".join(random.choice(self.bases) for _ in range(length))

    def _mutate(self, dna: str) -> str:
        result = list(dna)
        for i in range(len(result)):
            if random.random() < self.mut_rate:
                result[i] = random.choice(self.bases)

        codons = ["".join(result[i:i+3]) for i in range(0, len(result)-2, 3)]
        new_codons = []
        for codon in codons:
            r = random.random()
            if r < self.indel_rate:
                pass
            elif r < self.indel_rate * 2:
                new_codons.append("".join(random.choice(self.bases) for _ in range(3)))
                new_codons.append(codon)
            else:
                new_codons.append(codon)

        return "".join(new_codons) or self._rand()

    def _crossover_homologous(self, p1: str, p2: str) -> Tuple[str, str]:
        starts1 = [i for i in range(0, len(p1)-2, 3) if p1[i:i+3] == "ATG"]
        starts2 = [i for i in range(0, len(p2)-2, 3) if p2[i:i+3] == "ATG"]

        if starts1 and starts2:
            pt1 = random.choice(starts1)
            pt2 = random.choice(starts2)
            min_len = min(len(p1) - pt1, len(p2) - pt2)
            if min_len > 3:
                offset = random.randint(3, min_len - 1)
                c1 = p1[:pt1 + offset] + p2[pt2 + offset:]
                c2 = p2[:pt2 + offset] + p1[pt1 + offset:]
                c1 = c1[:(len(c1)//3)*3]
                c2 = c2[:(len(c2)//3)*3]
                return c1 or p1, c2 or p2

        pt = random.randint(1, min(len(p1), len(p2)) // 3 - 1) * 3
        return p1[:pt] + p2[pt:], p2[:pt] + p1[pt:]

    def _fitness(self, dna: str, parasite: Optional[str] = None) -> float:
        code = self.transcriptor.transcribe(dna)
        score = self.fitness_eval.evaluate(code)

        if dna.startswith("ATG"): score += 3.0
        if any(dna.endswith(s) for s in ["TAA", "TAG", "TGA"]): score += 3.0

        if parasite:
            similarity = sum(a == b for a, b in zip(dna, parasite)) / max(len(dna), len(parasite))
            score -= similarity * 2.0

        return max(0.0, score) / (len(self.target_kw) * 2 + 14)

    def _entropy_bonus(self, population: List[str]) -> Dict[str, float]:
        bonuses = {}
        for dna in population:
            total_dist = 0
            for other in population:
                if other is not dna:
                    min_len = min(len(dna), len(other))
                    total_dist += sum(a != b for a, b in zip(dna[:min_len], other[:min_len]))
                    total_dist += abs(len(dna) - len(other))
            avg_dist = total_dist / max(1, len(population) - 1)
            bonuses[id(dna)] = avg_dist / max(len(dna), 1) * 0.5
        return bonuses

    def _niche_partition(self, scored: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        if self.niche_count <= 1:
            return scored
        niche_size = max(1, len(scored) // self.niche_count)
        result = []
        for n in range(self.niche_count):
            start = n * niche_size
            end = start + niche_size if n < self.niche_count - 1 else len(scored)
            niche = scored[start:end]
            result.extend(niche[:max(1, len(niche) // 2)])
        return result

    def _register_phylo(self, dna: str, fitness: float, gen: int,
                         parent_id: Optional[str] = None) -> PhyloNode:
        node = PhyloNode(dna=dna, fitness=fitness, generation=gen, parent_id=parent_id)
        self.phylo_nodes[node.node_id] = node
        if parent_id and parent_id in self.phylo_nodes:
            self.phylo_nodes[parent_id].children.append(node)
        elif parent_id is None:
            self.phylo_roots.append(node)
        return node

    def export_newick(self, path: str = "phylogeny.nwk"):
        if not self.phylo_roots:
            return
        trees = [r.to_newick() for r in self.phylo_roots]
        newick = ";\n".join(trees) + ";\n"
        Path(path).write_text(newick, encoding="utf-8")
        print(f"Phylogenie Newick -> {path}")

    def export_history(self, path: str = "evolution_history.json"):
        Path(path).write_text(json.dumps(self.history, indent=2), encoding="utf-8")
        print(f"Historique evolution -> {path}")

    def evolve(self) -> str:
        print(f"Evolution v2 — cible: {', '.join(self.target_kw)}"
              f" | niches: {self.niche_count}"
              f" | coevolution: {self.coevolve}")

        best_dna, best_fit = self.pop[0], -1.0

        for dna in self.pop[:5]:
            self._register_phylo(dna, 0.0, 0)

        for g in range(self.gens):
            entropy_bonuses = self._entropy_bonus(self.pop)
            parasite = random.choice(self.parasite_pop) if self.parasite_pop else None

            scored = sorted(
                [(dna, self._fitness(dna, parasite) + entropy_bonuses.get(id(dna), 0))
                 for dna in self.pop],
                key=lambda x: x[1], reverse=True
            )

            scored = self._niche_partition(scored)

            best_dna, best_fit = scored[0]

            for dna, fit in scored[:3]:
                self._register_phylo(dna, fit, g)

            self.history.append({
                "generation": g,
                "best_fitness": round(best_fit, 4),
                "avg_fitness": round(sum(f for _, f in scored) / len(scored), 4),
                "pop_size": len(self.pop),
                "best_dna_len": len(best_dna),
            })

            if best_fit >= 0.95:
                print(f"Convergence anticipee a la generation {g}")
                break

            if g % 5 == 0:
                print(f"Gen {g:03d} | Fitness: {best_fit:.4f} | "
                      f"Pop: {len(self.pop)} | Len: {len(best_dna)} bp")

            elite_count = max(1, len(scored) // 10)
            new_pop = [s[0] for s in scored[:elite_count]]

            parents = [s[0] for s in scored[:max(2, len(scored) // 2)]]
            while len(new_pop) < self.pop_size:
                p1, p2 = random.choices(parents, k=2)
                c1, c2 = self._crossover_homologous(p1, p2)
                new_pop.extend([self._mutate(c1), self._mutate(c2)])

            self.pop = new_pop[:self.pop_size]

            if self.coevolve and self.parasite_pop:
                p_scored = sorted(
                    [(p, self._fitness(p)) for p in self.parasite_pop],
                    key=lambda x: x[1]
                )
                self.parasite_pop = [p[0] for p in p_scored[:len(self.parasite_pop)//2]]
                while len(self.parasite_pop) < self.pop_size // 2:
                    p1, p2 = random.choices(self.parasite_pop, k=2)
                    c1, _ = self._crossover_homologous(p1, p2)
                    self.parasite_pop.append(self._mutate(c1))

        print(f"Fitness finale: {best_fit:.4f} | Longueur: {len(best_dna)} bp")
        return best_dna


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Bio-Compiler v2.0 — ADN multi-langages")
    parser.add_argument("--dna", help="Sequence ADN manuelle")
    parser.add_argument("--lang", choices=list(LANG_PROFILES), default="python")
    parser.add_argument("--slot", default="./slot", help="Dossier des fichiers .prot")
    parser.add_argument("--evolve", action="store_true", help="Activer l'algorithme genetique")
    parser.add_argument("--target-kw", nargs="+", default=["for", "if", "try", "print"])
    parser.add_argument("--gens", type=int, default=40)
    parser.add_argument("--pop", type=int, default=30)
    parser.add_argument("--mut-rate", type=float, default=0.02)
    parser.add_argument("--indel-rate", type=float, default=0.005)
    parser.add_argument("--niches", type=int, default=3)
    parser.add_argument("--coevolve", action="store_true")
    parser.add_argument("--ext-codons", default=None)
    parser.add_argument("--output", help="Fichier de sortie")
    parser.add_argument("--export-fasta", action="store_true")
    parser.add_argument("--export-newick", action="store_true")
    parser.add_argument("--export-history", action="store_true")
    args = parser.parse_args()

    genetic_code = load_genetic_code(args.ext_codons)
    loader = ProteinLoader(args.slot)
    dna = args.dna.upper() if args.dna else None

    engine = None
    if args.evolve:
        engine = DNAEvolutionEngine(
            target_keywords = args.target_kw,
            pop_size    = args.pop,
            gens        = args.gens,
            mut_rate    = args.mut_rate,
            indel_rate  = args.indel_rate,
            lang        = args.lang,
            loader      = loader,
            genetic_code= genetic_code,
            niche_count = args.niches,
            coevolve    = args.coevolve,
        )
        dna = engine.evolve()
        print(f"Sequence optimisee : {dna}")

    if not dna:
        print("Aucune sequence. Utilisez --dna ou --evolve")
        sys.exit(1)

    print(f"Transcription -> {args.lang.upper()}...")
    transcriptor = DNAToCodeTranscriptor(args.lang, loader, genetic_code)
    code = transcriptor.transcribe(dna)

    ext = LANG_PROFILES[args.lang]["ext"]
    out_file = args.output or f"bio_program_{args.lang}{ext}"
    Path(out_file).write_text(code, encoding="utf-8")
    print(f"Code genere -> {out_file}")

    if args.export_fasta:
        fasta = f">BioCode_Evolved_{args.lang}\n{dna}\n"
        Path("sequence.fasta").write_text(fasta, encoding="utf-8")
        print("FASTA -> sequence.fasta")

    if args.export_newick and engine:
        engine.export_newick("phylogeny.nwk")

    if args.export_history and engine:
        engine.export_history("evolution_history.json")


if __name__ == "__main__":
    main()
