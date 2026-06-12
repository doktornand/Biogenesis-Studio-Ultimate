#!/usr/bin/env python3
"""
prot_generator_multilang.py — Moteur de generation v3.1 (Corrigé & Robuste)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NOUVEAUTES v3.1 :
• Parsing robuste : Plus d'erreur 'NoneType' sur les regex mal formatées.
• Tolérance aux espaces dans les directives (ex: {{ mutate: 0.03 }}).
• Correction automatique des opérateurs C# (&& -> and) pour l'évaluation Python.
• Messages d'avertissement clairs en cas de valeur non numérique dans {{repeat:}}.
"""
import json, re, math, random, hashlib, os, copy
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum, auto

# ══════════════════════════════════════════════════════════════════════════════
# PROFILS DE LANGAGE
# ══════════════════════════════════════════════════════════════════════════════
LANG_PROFILES: Dict[str, Dict[str, Any]] = {
"python": {
"ext": ".py", "comment": "#", "indent": "    ",
"class_def": "class BioProgram:", "init_method": "def __init__(self):",
"exec_method": "def execute(self):", "state_var": "self._cellularState",
"entropy_var": "self._entropy", "organelles": "self._organelles",
"epigenetic_memory": "self._epigeneticMemory", "cell_generation": "self._cellGeneration",
"telomere_length": "self._telomereLength", "stuck_counter": "self._stuckCounter",
"imports_block": "import random\nimport math\nfrom datetime import datetime\n",
"random_method": "random.random()", "randint_method": "random.randint",
"console_write": "print",
"syntax": {
"if": "if {cond}:", "elif": "elif {cond}:", "else": "else:",
"for": "for {var} in range({count}):", "while": "while {cond}:",
"try": "try:", "except": "except Exception as e:",
"inc_state": "self._cellularState += 1", "dec_state": "self._cellularState = max(0, self._cellularState - 1)",
}
},
"csharp": {
"ext": ".cs", "comment": "//", "indent": "    ",
"class_def": "public class BioProgram", "init_method": "public BioProgram()",
"exec_method": "public void Execute()", "state_var": "_cellularState",
"entropy_var": "_entropy", "organelles": "_organelles",
"epigenetic_memory": "_epigeneticMemory", "cell_generation": "_cellGeneration",
"telomere_length": "_telomereLength", "stuck_counter": "_stuckCounter",
"imports_block": "using System;\nusing System.Collections.Generic;\n",
"random_method": "new Random().NextDouble()", "randint_method": "new Random().Next",
"console_write": "Console.WriteLine",
"syntax": {
"if": "if ({cond})", "elif": "else if ({cond})", "else": "else",
"for": "for (int {var} = 0; {var} < {count}; {var}++)", "while": "while ({cond})",
"try": "try", "except": "catch (Exception e)",
"inc_state": "_cellularState++", "dec_state": "_cellularState = Math.Max(0, _cellularState - 1)",
}
},
"javascript": {
"ext": ".js", "comment": "//", "indent": "  ",
"class_def": "class BioProgram", "init_method": "constructor()",
"exec_method": "execute()", "state_var": "this._cellularState",
"entropy_var": "this._entropy", "organelles": "this._organelles",
"epigenetic_memory": "this._epigeneticMemory", "cell_generation": "this._cellGeneration",
"telomere_length": "this._telomereLength", "stuck_counter": "this._stuckCounter",
"imports_block": "", "random_method": "Math.random()",
"randint_method": "(min, max) => Math.floor(Math.random() * (max - min) + min)",
"console_write": "console.log",
"syntax": {
"if": "if ({cond})", "elif": "else if ({cond})", "else": "else",
"for": "for (let {var} = 0; {var} < {count}; {var}++)", "while": "while ({cond})",
"try": "try {{", "except": "}} catch (e) {{",
"inc_state": "this._cellularState++", "dec_state": "this._cellularState = Math.max(0, this._cellularState - 1)",
}
},
"rust": {
"ext": ".rs", "comment": "//", "indent": "    ",
"class_def": "pub struct BioProgram", "init_method": "pub fn new() -> Self",
"exec_method": "pub fn execute(&mut self)", "state_var": "self.cellular_state",
"entropy_var": "self.entropy", "organelles": "self.organelles",
"epigenetic_memory": "self.epigenetic_memory", "cell_generation": "self.cell_generation",
"telomere_length": "self.telomere_length", "stuck_counter": "self.stuck_counter",
"imports_block": "use rand::Rng;\nuse std::time::SystemTime;\n",
"random_method": "rand::thread_rng().gen::<f64>()", "randint_method": "rand::thread_rng().gen_range",
"console_write": "println!",
"syntax": {
"if": "if {cond}", "elif": "else if {cond}", "else": "else",
"for": "for {var} in 0..{count}", "while": "while {cond}",
"try": "// Rust uses Result type", "except": "// Error handling with match",
"inc_state": "self.cellular_state += 1", "dec_state": "self.cellular_state = if self.cellular_state > 0 {{ self.cellular_state - 1 }} else {{ 0 }}",
}
},
"go": {
"ext": ".go", "comment": "//", "indent": "\t",
"class_def": "type BioProgram struct", "init_method": "func NewBioProgram() *BioProgram",
"exec_method": "func (b *BioProgram) Execute()", "state_var": "b.cellularState",
"entropy_var": "b.entropy", "organelles": "b.organelles",
"epigenetic_memory": "b.epigeneticMemory", "cell_generation": "b.cellGeneration",
"telomere_length": "b.telomereLength", "stuck_counter": "b.stuckCounter",
"imports_block": "import (\n\t\"fmt\"\n\t\"math/rand\"\n\t\"time\"\n)\n",
"random_method": "rand.Float64()", "randint_method": "rand.Intn",
"console_write": "fmt.Println",
"syntax": {
"if": "if {cond}", "elif": "else if {cond}", "else": "else",
"for": "for {var} := 0; {var} < {count}; {var}++", "while": "for {cond}",
"try": "// Go uses error returns", "except": "if err != nil",
"inc_state": "b.cellularState++", "dec_state": "if b.cellularState > 0 {{ b.cellularState-- }}",
}
}
}

# ══════════════════════════════════════════════════════════════════════════════
# EXCEPTIONS ET AST
# ══════════════════════════════════════════════════════════════════════════════
class ProtGenerationError(Exception): pass
class EpigeneticSilencingError(Exception): pass
class UnsupportedLanguageError(Exception): pass

class NodeType(Enum):
    RAW = auto(); DIRECTIVE = auto(); COND = auto(); REPEAT = auto()
    MUTATE = auto(); OSCILLATE = auto(); QUINE = auto(); PLASMID = auto()
    TRANSPOSON = auto(); OPERON = auto(); SELF_REF = auto(); CA_STATE = auto()

@dataclass
class ASTNode:
    ntype: NodeType
    value: str = ""
    children: List["ASTNode"] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationContext:
    globals: Dict[str, Any]
    variables: Dict[str, Any]
    meta: Dict[str, Any]
    loop_vars: Dict[str, int]
    recursion_stack: List[str]
    conway_rules: Dict[str, List[str]]
    transposons: Dict[str, Dict] = field(default_factory=dict)
    epigenetic: List[str] = field(default_factory=list)
    generation: int = 0
    plasmids: Dict[str, Any] = field(default_factory=dict)
    operons: List[Dict] = field(default_factory=list)
    lang_profile: Dict[str, Any] = field(default_factory=dict)
    target_lang: str = "csharp"

# ══════════════════════════════════════════════════════════════════════════════
# EVALUATEUR ET PARSER (ROBUSTE)
# ══════════════════════════════════════════════════════════════════════════════
class SafeEvaluator:
    ALLOWED = {'abs','max','min','pow','sqrt','floor','ceil',
               'random','randint','choice','sin','cos','log','round'}
    def __init__(self):
        self._funcs = {
            'random': random.random, 'randint': random.randint,
            'choice': random.choice, 'abs': abs, 'max': max, 'min': min,
            'pow': pow, 'sqrt': math.sqrt, 'floor': math.floor,
            'ceil': math.ceil, 'sin': math.sin, 'cos': math.cos,
            'log': math.log, 'round': round
        }

    def eval(self, expr: str, ctx: GenerationContext) -> Any:
        namespace = {**self._funcs, **ctx.variables, **ctx.globals}
        expr = re.sub(r'\{\{global:(\w+)\}\}',
                      lambda m: str(ctx.globals.get(m.group(1), m.group(0))), expr)
        clean = re.sub(r'[^\w\s\+\-\*\/\(\)\.\%\&\|\<\>\=\!\,]', '', expr)
        try:
            return eval(clean, {"__builtins__": {}}, namespace)
        except Exception as e:
            return f"/* ExprError: {e} */"

class ProtParser:
    DIRECTIVE_RE = re.compile(r'\{\{(.*?)\}\}')

    def parse(self, lines: List[str]) -> List[ASTNode]:
        nodes, i = [], 0
        while i < len(lines):
            node, i = self._parse_line(lines, i)
            if node:
                nodes.append(node)
        return nodes

    def _parse_line(self, lines: List[str], i: int) -> Tuple[Optional[ASTNode], int]:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("{{if:"):
            return self._parse_conditional(lines, i)
        if stripped.startswith("{{repeat:"):
            return self._parse_repeat(lines, i)
        if stripped.startswith("{{mutate:"):
            match = re.search(r"{{mutate:\s*([\d.]+)\s*}}", stripped)
            prob = float(match.group(1)) if match else 0.0
            return self._parse_inline_block(lines, i, "{{endmutate}}", NodeType.MUTATE, lambda s: prob)
        if stripped.startswith("{{oscillate:"):
            match = re.search(r"{{oscillate:\s*(\d+)\s*}}", stripped)
            period = int(match.group(1)) if match else 1
            return self._parse_inline_block(lines, i, "{{endoscillate}}", NodeType.OSCILLATE, lambda s: period)
        if stripped.startswith("{{quine:}}"):
            return ASTNode(NodeType.QUINE), i + 1
        if stripped.startswith("{{transposon:"):
            match = re.search(r"{{transposon:\s*(\w+)\s*}}", stripped)
            tid = match.group(1) if match else "UNKNOWN"
            return ASTNode(NodeType.TRANSPOSON, value=tid), i + 1
        if stripped.startswith("{{plasmid:"):
            match = re.search(r"{{plasmid:\s*(\w+)\s*}}", stripped)
            pid = match.group(1) if match else "UNKNOWN"
            return ASTNode(NodeType.PLASMID, value=pid), i + 1
        if stripped.startswith("{{operon_check:"):
            match = re.search(r"{{operon_check:\s*(\w+)\s*}}", stripped)
            oid = match.group(1) if match else "UNKNOWN"
            return ASTNode(NodeType.OPERON, value=oid), i + 1
        if stripped.startswith("{{self_ref:"):
            match = re.search(r"{{self_ref:\s*(\w+)\s*}}", stripped)
            ref = match.group(1) if match else "UNKNOWN"
            return ASTNode(NodeType.SELF_REF, value=ref), i + 1
        if stripped.startswith("{{ca_state:"):
            match = re.search(r"{{ca_state:\s*(\S+)\s*}}", stripped)
            rule = match.group(1) if match else "UNKNOWN"
            return ASTNode(NodeType.CA_STATE, value=rule), i + 1

        return ASTNode(NodeType.RAW, value=line), i + 1

    def _parse_conditional(self, lines: List[str], start: int) -> Tuple[ASTNode, int]:
        node = ASTNode(NodeType.COND)
        i = start
        current_cond, current_lines = None, []
        depth = 0
        while i < len(lines):
            s = lines[i].strip()
            if s.startswith("{{if:") and i != start:
                depth += 1
            
            if s.startswith("{{endif}}"):
                if depth > 0:
                    depth -= 1
                    current_lines.append(lines[i])
                    i += 1
                    continue
                else:
                    if current_cond is not None:
                        sub = ASTNode(NodeType.COND, value=current_cond, children=self.parse(current_lines))
                        node.children.append(sub)
                    return node, i + 1

            if depth == 0:
                if s.startswith("{{if:"):
                    match = re.search(r"{{if:\s*(.*?)\s*}}", s)
                    current_cond = match.group(1) if match else "True"
                elif s.startswith("{{elif:"):
                    if current_cond is not None:
                        sub = ASTNode(NodeType.COND, value=current_cond, children=self.parse(current_lines))
                        node.children.append(sub)
                    match = re.search(r"{{elif:\s*(.*?)\s*}}", s)
                    current_cond = match.group(1) if match else "True"
                    current_lines = []
                elif s == "{{else}}":
                    if current_cond is not None:
                        sub = ASTNode(NodeType.COND, value=current_cond, children=self.parse(current_lines))
                        node.children.append(sub)
                    current_cond = "True"
                    current_lines = []
                else:
                    current_lines.append(lines[i])
            else:
                current_lines.append(lines[i])
            i += 1
        return node, i

    def _parse_repeat(self, lines: List[str], start: int) -> Tuple[ASTNode, int]:
        s = lines[start].strip()
        # Regex souple : accepte les espaces et les mots (variables)
        match = re.search(r"{{repeat:\s*([\w]+)\s*}}", s)
        if match:
            val_str = match.group(1)
            try:
                count = int(val_str)
            except ValueError:
                print(f"[⚠️ WARN] _parse_repeat: '{val_str}' n'est pas un entier. Valeur par défaut = 5.")
                count = 5
        else:
            print(f"[⚠️ WARN] _parse_repeat: Format invalide '{s}'. Valeur par défaut = 1.")
            count = 1

        block, end = self._extract_until(lines, start + 1, "{{endrepeat}}")
        node = ASTNode(NodeType.REPEAT, meta={"count": count, "raw_val": val_str if 'val_str' in locals() else str(count)},
                       children=self.parse(block))
        return node, end

    def _parse_inline_block(self, lines: List[str], start: int, end_marker: str,
                            ntype: NodeType, parse_val) -> Tuple[ASTNode, int]:
        val = parse_val(lines[start].strip())
        block, end = self._extract_until(lines, start + 1, end_marker)
        node = ASTNode(ntype, meta={"value": val}, children=self.parse(block))
        return node, end

    def _extract_until(self, lines: List[str], start: int, marker: str) -> Tuple[List[str], int]:
        out, i = [], start
        while i < len(lines) and lines[i].strip() != marker:
            out.append(lines[i])
            i += 1
        return out, i + 1

# ══════════════════════════════════════════════════════════════════════════════
# RENDERER MULTI-LANGAGES
# ══════════════════════════════════════════════════════════════════════════════
class ProtRenderer:
    def __init__(self, evaluator: SafeEvaluator, engine: "ProtEngine"):
        self.ev = evaluator
        self.engine = engine

    def render(self, nodes: List[ASTNode], ctx: GenerationContext, raw_template: List[str] = None) -> List[str]:
        out = []
        for node in nodes:
            out.extend(self._render_node(node, ctx, raw_template))
        return out

    def _render_node(self, node: ASTNode, ctx: GenerationContext, raw_template: List[str] = None) -> List[str]:
        profile = ctx.lang_profile
        indent = profile.get("indent", "    ")
        
        if node.ntype == NodeType.RAW:
            return [self._expand(node.value, ctx)]
        elif node.ntype == NodeType.COND:
            for branch in node.children:
                try:
                    ns = {**ctx.globals, **ctx.variables, **ctx.loop_vars}
                    # Correction automatique des opérateurs C# pour l'éval Python
                    clean_cond = branch.value.replace("& &", "and").replace("&&", "and")
                    if eval(clean_cond, {"__builtins__": {}}, ns):
                        return self.render(branch.children, ctx, raw_template)
                except Exception as e:
                    print(f"[⚠️ WARN] Échec évaluation condition '{branch.value}': {e}")
                    pass
            return []
        elif node.ntype == NodeType.REPEAT:
            out = []
            for n in range(node.meta["count"]):
                ctx.loop_vars["loop_var"] = n
                out.extend(self.render(node.children, ctx, raw_template))
            return out
        elif node.ntype == NodeType.MUTATE:
            prob = node.meta["value"]
            if random.random() < prob:
                return self.render(node.children, ctx, raw_template)
            return []
        elif node.ntype == NodeType.OSCILLATE:
            period = node.meta["value"]
            if ctx.generation % period == 0:
                return self.render(node.children, ctx, raw_template)
            return []
        elif node.ntype == NodeType.QUINE:
            if raw_template:
                comment = profile.get("comment", "//")
                lines = [f"{indent}{comment} [QUINE] Je m'imprime moi-meme :"]
                for tl in raw_template[:8]:
                    escaped = self._escape_for_lang(tl, ctx.target_lang)
                    if ctx.target_lang == "python":
                        lines.append(f'{indent}{profile["console_write"]}("{escaped}")')
                    elif ctx.target_lang in ["csharp", "javascript", "go"]:
                        lines.append(f'{indent}{profile["console_write"]}("{escaped}");')
                    elif ctx.target_lang == "rust":
                        lines.append(f'{indent}{profile["console_write"]}!("{escaped}");')
                return lines
            return [f"{indent}// [QUINE] Template source indisponible"]
        elif node.ntype == NodeType.PLASMID:
            pid = node.value
            plasmid = ctx.plasmids.get(pid)
            if plasmid:
                lines = [f"{indent}// [PLASMID:{pid}] Insertion"]
                for l in plasmid.get("sequence", []):
                    expanded = self._expand(l, ctx)
                    lines.append(f"{indent}{expanded}")
                return lines
            return [f"{indent}// [PLASMID:{pid}] non trouve"]
        elif node.ntype == NodeType.TRANSPOSON:
            tid = node.value
            tp = ctx.transposons.get(tid)
            if tp and random.random() < tp.get("jump_prob", 0.1):
                effect = self._expand(tp.get("effect", ""), ctx)
                return [f"{indent}// [TRANSPOSON:{tid}] Saut detecte", f"{indent}{effect}"]
            return [f"{indent}// [TRANSPOSON:{tid}] Silencieux"]
        elif node.ntype == NodeType.OPERON:
            oid = node.value
            for op in ctx.operons:
                if op["id"] == oid:
                    cond = self._expand(op.get("promoter_condition", "False"), ctx)
                    try:
                        ns = {**ctx.globals, **ctx.variables}
                        clean_cond = cond.replace("& &", "and").replace("&&", "and")
                        active = eval(clean_cond, {"__builtins__": {}}, ns)
                    except Exception:
                        active = False
                    status = "active" if active else "silencieux"
                    return [f"{indent}// [OPERON:{oid}] Promoteur {status}"]
            return [f"{indent}// [OPERON:{oid}] non trouve"]
        elif node.ntype == NodeType.SELF_REF:
            ref_id = node.value
            sub_def = self.engine._find_protein(ref_id)
            if sub_def:
                code = self.engine._generate_protein(sub_def, depth=len(ctx.recursion_stack))
                return code.splitlines()
            return [f"{indent}// self_ref:{ref_id} non trouve"]
        elif node.ntype == NodeType.CA_STATE:
            rule = node.value
            rules = ctx.conway_rules.get(rule, [])
            return [self._expand(r, ctx) for r in rules]
        else:
            return [f"{indent}// [UNKNOWN NODE: {node.ntype}]"]

    def _escape_for_lang(self, text: str, lang: str) -> str:
        return text.replace('"', '\\"')

    def _expand(self, line: str, ctx: GenerationContext) -> str:
        def repl(m):
            return str(self._resolve(m.group(1).strip(), ctx))
        return re.sub(r"\{\{(.*?)\}\}", repl, line)

    def _resolve(self, directive: str, ctx: GenerationContext) -> Any:
        profile = ctx.lang_profile
        if directive.startswith("expr:"):
            return self.ev.eval(directive[5:], ctx)
        if directive.startswith("meta:"):
            return ctx.meta.get(directive[5:], f"/* meta:{directive[5:]} */")
        if directive.startswith("global:"):
            return ctx.globals.get(directive[7:], f"/* global:{directive[7:]} */")
        if directive == "loop_var" or directive.startswith("loop_var"):
            return ctx.loop_vars.get("loop_var", "0")
        if directive.startswith("comment"):
            return profile.get("comment", "// ")
        if directive.startswith("state_var"):
            return profile.get("state_var", ctx.variables.get("state_var", "_cellularState"))
        if directive.startswith("entropy"):
            return profile.get("entropy_var", ctx.variables.get("entropy", "_entropy"))
        if directive.startswith("gen_count"):
            return ctx.generation
        if directive.startswith("random_choice:"):
            choices = json.loads(directive[14:])
            return random.choice(choices)
        if directive in ctx.epigenetic:
            raise EpigeneticSilencingError(f"Directive {directive} silencee")
        return ctx.variables.get(directive, ctx.globals.get(directive, f"/* var:{directive} */"))

# ══════════════════════════════════════════════════════════════════════════════
# MOTEUR PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
class ProtEngine:
    def __init__(self, config_path: str, output_dir: str = "./slot",
                 generation: int = 0, target_lang: str = "csharp"):
        self.config = json.loads(Path(config_path).read_text())
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.target_lang = target_lang.lower()
        if self.target_lang not in LANG_PROFILES:
            raise UnsupportedLanguageError(f"Langage '{target_lang}' non supporte. Choisir parmi: {list(LANG_PROFILES.keys())}")
        
        self.lang_profile = LANG_PROFILES[self.target_lang]
        self.evaluator = SafeEvaluator()
        self.parser = ProtParser()
        self.renderer = ProtRenderer(self.evaluator, self)
        self.cache: Dict[str, str] = {}
        self.checksums: Dict[str, str] = {}
        self.generation = generation
        self.manifest: List[Dict] = []
        self._plasmids = {p["id"]: p for p in self.config.get("plasmids", [])}
        self._operons = self.config.get("operons", [])

    def _resolve_inheritance(self, prot_def: Dict) -> Dict:
        parent_id = prot_def.get("extends")
        if not parent_id:
            return prot_def
        parent = self._find_protein(parent_id)
        if not parent:
            raise ProtGenerationError(f"Parent '{parent_id}' introuvable pour '{prot_def['id']}'")
        
        merged = copy.deepcopy(parent)
        merged.update({k: v for k, v in prot_def.items() if k not in ("extends", "override")})
        
        for dotted_key, val in prot_def.get("override", {}).items():
            keys = dotted_key.split(".")
            target = merged
            for k in keys[:-1]:
                target = target.setdefault(k, {})
            target[keys[-1]] = val
            
        if "template" in prot_def:
            merged["template"] = prot_def["template"]
        merged["id"] = prot_def["id"]
        merged["filename"] = prot_def.get("filename", f"{prot_def['id']}{self.lang_profile['ext']}")
        return merged

    def generate_all(self):
        proteins = self.config.get("proteins", [])
        lang_name = self.target_lang.upper()
        print(f"Generation v3.1 — {len(proteins)} proteines, generation {self.generation}, langage {lang_name}...")
        for prot_def in proteins:
            self._generate_protein(prot_def)
        self._write_manifest()
        print(f"Fini — {len(self.cache)} fichiers .{self.target_lang} -> {self.output_dir}")

    def _generate_protein(self, prot_def: Dict, depth: int = 0) -> str:
        prot_id = prot_def["id"]
        max_depth = self.config.get("global", {}).get("max_recursion_depth", 6)
        if depth > max_depth:
            raise ProtGenerationError(f"Recursion ({depth}) pour '{prot_id}'")
        if prot_id in self.cache:
            return self.cache[prot_id]

        resolved = self._resolve_inheritance(prot_def)
        ctx = GenerationContext(
            globals=self.config.get("global", {}),
            variables=resolved.get("variables", {}),
            meta=resolved.get("meta", {}),
            loop_vars={},
            recursion_stack=[prot_id],
            conway_rules=resolved.get("conway_rules", {}),
            transposons=resolved.get("transposons", {}),
            epigenetic=resolved.get("epigenetic_markers", []),
            generation=self.generation,
            plasmids=self._plasmids,
            operons=self._operons,
            lang_profile=self.lang_profile,
            target_lang=self.target_lang,
        )
        
        raw_template = self._resolve_parent_refs(resolved.get("template", []), resolved)
        sub_proteins = resolved.get("sub_proteins", {})
        ast = self.parser.parse(raw_template)
        ast = self._inject_sub_proteins(ast, sub_proteins)
        code_lines = self._generate_class_wrapper(ast, ctx, raw_template)
        code = "\n".join(code_lines)
        
        chk = hashlib.sha256(code.encode()).hexdigest()[:12]
        filename = resolved.get("filename", f"{prot_id}{self.lang_profile['ext']}")
        out_path = self.output_dir / filename
        
        if self.checksums.get(prot_id) == chk and out_path.exists():
            print(f"  {filename} inchange (checksum {chk})")
        else:
            out_path.write_text(code, encoding="utf-8")
            self.checksums[prot_id] = chk
            print(f"  {filename} ({len(code_lines)} lignes, lang={self.target_lang})")
            
        self.cache[prot_id] = code
        self.manifest.append({
            "id": prot_id, "filename": filename, "checksum": chk,
            "generation": self.generation, "lines": len(code_lines),
            "language": self.target_lang, "epigenetic_markers": ctx.epigenetic,
            "extends": prot_def.get("extends"),
        })
        return code

    def _generate_class_wrapper(self, ast: List[ASTNode], ctx: GenerationContext, raw_template: List[str]) -> List[str]:
        profile = ctx.lang_profile
        indent = profile.get("indent", "    ")
        comment = profile.get("comment", "//")
        code = []
        code.append(profile["imports_block"])
        code.append(f"{comment} " + "=" * 50)
        code.append(f"{comment} GENERATION AUTOMATIQUE — Bio-Compiler v3.1")
        code.append(f"{comment} Langage: {self.target_lang.upper()}")
        code.append(f"{comment} " + "=" * 50)
        code.append("")
        code.append(f"{profile['class_def']} {{")
        code.append(f"{indent}{comment} Attributs cellulaires")
        code.append(f"{indent}{profile['state_var']} = 0")
        code.append(f"{indent}{profile['organelles']} = []")
        code.append("")
        code.append(f"{indent}{profile['init_method']} {{")
        code.append(f"{indent*2}{comment} Initialisation cellulaire")
        rendered = self.renderer.render(ast, ctx, raw_template)
        for line in rendered:
            if line.strip():
                code.append(f"{indent*2}{line}")
            else:
                code.append("")
        code.append(f"{indent}}}")
        code.append("")
        code.append(f"{indent}{profile['exec_method']} {{")
        code.append(f"{indent*2}{comment} Execution du programme")
        code.append(f"{indent*2}{profile['console_write']}(\"Execution BioProgram\")")
        code.append(f"{indent}}}")
        code.append("}")
        return code

    def _resolve_parent_refs(self, template: List[str], resolved: Dict) -> List[str]:
        out = []
        for line in template:
            m = re.search(r"\{\{parent:\s*(\w+)\s*\}\}", line)
            if m:
                parent_id = m.group(1)
                parent = self._find_protein(parent_id)
                if parent:
                    out.extend(parent.get("template", []))
                else:
                    out.append(f"    // parent:{parent_id} introuvable")
            else:
                out.append(line)
        return out

    def _inject_sub_proteins(self, ast: List[ASTNode], sub_proteins: Dict) -> List[ASTNode]:
        for node in ast:
            if node.ntype == NodeType.SELF_REF and node.value in sub_proteins:
                lines = sub_proteins[node.value]
                node.ntype = NodeType.RAW
                node.value = "\n".join(lines)
                node.children = []
            elif node.children:
                node.children = self._inject_sub_proteins(node.children, sub_proteins)
        return ast

    def _find_protein(self, prot_id: str) -> Optional[Dict]:
        for p in self.config.get("proteins", []):
            if p.get("id") == prot_id:
                return p
        return None

    def _write_manifest(self):
        manifest_path = self.output_dir / f"manifest_{self.target_lang}.json"
        manifest_path.write_text(
            json.dumps({
                "generation": self.generation,
                "language": self.target_lang,
                "proteins": self.manifest
            }, indent=2),
            encoding="utf-8"
        )
        print(f"  Manifeste -> {manifest_path}")

# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════
def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Distillateur de proteines v3.1 — Multi-langages (Robuste)",
        epilog=f"Langages supportes: {list(LANG_PROFILES.keys())}"
    )
    parser.add_argument("config", help="Chemin vers le JSON de configuration")
    parser.add_argument("-o", "--output", default="./slot", help="Dossier de sortie")
    parser.add_argument("-g", "--generation", type=int, default=0, help="Numero de generation")
    parser.add_argument("-l", "--lang", default="csharp", choices=list(LANG_PROFILES.keys()), help="Langage cible")
    args = parser.parse_args()
    
    engine = ProtEngine(args.config, args.output, generation=args.generation, target_lang=args.lang)
    engine.generate_all()

if __name__ == "__main__":
    main()