# Shared helpers for writing TMDL semantic models from Python (used by projects/*/build_model.py).
import json, os, re, uuid

T = "\t"


class Model:
    def __init__(self, definition_dir, namespace):
        self.DEF = definition_dir
        self.NS = uuid.uuid5(uuid.NAMESPACE_URL, namespace)
        self.tables, self.measures, self.categories = [], [], {}
        os.makedirs(os.path.join(self.DEF, "tables"), exist_ok=True)
        for f in os.listdir(os.path.join(self.DEF, "tables")):
            os.remove(os.path.join(self.DEF, "tables", f))

    def tag(self, *path):
        return str(uuid.uuid5(self.NS, "/".join(path)))

    @staticmethod
    def q(name):
        return f"'{name}'" if re.search(r"[^A-Za-z0-9_]", name) else name

    def column(self, table, name, dtype, fmt=None, hidden=False, key=False, summarize="none", sort_by=None, date_only=False, desc=None):
        q = self.q
        L = [f"{T}/// {desc}"] if desc else []
        L += [f"{T}column {q(name)}", f"{T*2}dataType: {dtype}"]
        if key:
            L.append(f"{T*2}isKey")
        if hidden:
            L.append(f"{T*2}isHidden")
        if fmt:
            L.append(f"{T*2}formatString: {fmt}")
        L += [f"{T*2}lineageTag: {self.tag(table, 'col', name)}", f"{T*2}summarizeBy: {summarize}", f"{T*2}sourceColumn: {name}"]
        if sort_by:
            L.append(f"{T*2}sortByColumn: {q(sort_by)}")
        L += ["", f"{T*2}annotation SummarizationSetBy = Automatic"]
        if date_only:
            L += ["", f"{T*2}annotation UnderlyingDateTimeDataType = Date"]
        return "\n".join(L) + "\n\n"

    def table(self, name, desc, cols, m_lines, props=(), measures=""):
        q = self.q
        body = "\n".join(f"{T*4}{l}" for l in m_lines)
        s = f"/// {desc}\ntable {q(name)}\n{T}lineageTag: {self.tag(name)}\n" + "".join(f"{T}{p}\n" for p in props) + "\n"
        s += measures + "".join(cols) + f"{T}partition {q(name)} = m\n{T*2}mode: import\n{T*2}source =\n{body}\n\n"
        s += f"{T}annotation PBI_ResultType = Table\n"
        with open(os.path.join(self.DEF, "tables", f"{name}.tmdl"), "w", encoding="utf-8", newline="\n") as f:
            f.write(s)
        self.tables.append(name)

    @staticmethod
    def excel(workbook, item, steps, types):
        out = ["let", f'{T}Source = Excel.Workbook(File.Contents(DataFolder & "{workbook}"), null, true),',
               f'{T}#"{item} Table" = Source{{[Item="{item}",Kind="Table"]}}[Data],']
        prev = f'#"{item} Table"'
        for sname, expr in steps:
            out.append(f'{T}#"{sname}" = {expr.format(prev=prev)},')
            prev = f'#"{sname}"'
        tl = ", ".join(f'{{"{c}", {t}}}' for c, t in types)
        return out + [f'{T}#"Set Column Types" = Table.TransformColumnTypes({prev}, {{{tl}}})', "in", f'{T}#"Set Column Types"']

    def add(self, name, folder, fmt, desc, *lines):
        self.measures.append((name, folder, fmt, desc, list(lines)))

    def measures_text(self):
        ms = ""
        for name, folder, fmt, desc, lines in self.measures:
            ms += f"{T}/// {desc}\n"
            ms += f"{T}measure {self.q(name)} = {lines[0]}\n" if len(lines) == 1 else f"{T}measure {self.q(name)} =\n" + "".join(f"{T*3}{l}\n" for l in lines)
            if fmt:
                ms += f"{T*2}formatString: {fmt}\n"
            if name in self.categories:
                ms += f"{T*2}dataCategory: {self.categories[name]}\n"
            ms += f"{T*2}displayFolder: {folder}\n{T*2}lineageTag: {self.tag('_Measures', 'measure', name)}\n\n"
        return ms

    def finish(self, table_order, relationships, data_folder_default, workbook_note):
        self.table("_Measures", "Holds the report measures; its only column is a hidden placeholder",
                   [self.column("_Measures", "Column1", "string", hidden=True)],
                   ["let", f"{T}Source = #table(type table [Column1 = text], {{}})", "in", f"{T}Source"], measures=self.measures_text())
        order = table_order + ["_Measures"]
        with open(os.path.join(self.DEF, "model.tmdl"), "w", newline="\n") as f:
            f.write("model Model\n\tculture: en-US\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-US\n\tdataAccessOptions\n"
                    "\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\nannotation __PBI_TimeIntelligenceEnabled = 0\n\n"
                    f"annotation PBI_QueryOrder = {json.dumps(['DataFolder'] + order, separators=(',', ':'))}\n\n" +
                    "".join(f"ref table {self.q(t)}\n" for t in order) + "\n")
        with open(os.path.join(self.DEF, "expressions.tmdl"), "w", newline="\n") as f:
            f.write(f'/// {workbook_note}\nexpression DataFolder = "{data_folder_default}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
                    f"\tlineageTag: {self.tag('expr', 'DataFolder')}\n\n\tannotation PBI_ResultType = Text\n\n")
        with open(os.path.join(self.DEF, "relationships.tmdl"), "w", newline="\n") as f:
            for a, b in relationships:
                f.write(f"relationship {self.tag('rel', a, b)}\n\tfromColumn: {a}\n\ttoColumn: {b}\n\n")
        db = os.path.join(self.DEF, "database.tmdl")
        if not os.path.exists(db):
            with open(db, "w", newline="\n") as f:
                f.write("database\n\tcompatibilityLevel: 1567\n\n")


def cy(expr):
    return ["VAR _LatestYear = MAX ( 'Date'[Year] )", "RETURN", f"    CALCULATE ( {expr}, KEEPFILTERS ( 'Date'[Year] = _LatestYear ) )"]


def py(expr):
    return ["VAR _LatestYear = MAX ( 'Date'[Year] )", "RETURN", "    CALCULATE (", f"        CALCULATE ( {expr}, SAMEPERIODLASTYEAR ( 'Date'[Date] ) ),",
            "        KEEPFILTERS ( 'Date'[Year] = _LatestYear )", "    )"]


def growth(cur, prev):
    return [f"VAR _Current = {cur}", f"VAR _Previous = {prev}", "RETURN", "    DIVIDE ( _Current - _Previous, _Previous )"]


def diff(cur, prev, scale=1):
    s = f" * {scale}" if scale != 1 else ""
    return [f"VAR _Current = {cur}", f"VAR _Previous = {prev}", "RETURN", f"    IF ( NOT ISBLANK ( _Previous ) && NOT ISBLANK ( _Current ), ( _Current - _Previous ){s} )"]
