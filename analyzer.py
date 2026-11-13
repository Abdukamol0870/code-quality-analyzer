
import ast
import re
from collections import Counter


# Python kodini statik tahlil qilish
class CodeAnalyzer(ast.NodeVisitor):

    def __init__(self, source):
        self.source = source
        self.lines = source.splitlines()
        self.issues = []
        self.tree = None

    def add_issue(self, rule, severity, line, title, message, suggestion):
        self.issues.append({
            "rule": rule,
            "severity": severity,
            "line": line or 1,
            "title": title,
            "message": message,
            "suggestion": suggestion
        })

    def analyze(self):
        try:
            self.tree = ast.parse(self.source)
        except SyntaxError as error:
            self.add_issue(
                "SYNTAX", "high", error.lineno,
                "Sintaksis xatosi",
                error.msg,
                "Python sintaksisini tekshiring va xatoni tuzating."
            )
            return self.make_result()

        self.check_functions()
        self.check_classes()
        self.check_naming()
        self.check_magic_numbers()
        self.check_unused_imports()
        self.check_duplicate_lines()
        self.check_dead_code()

        return self.make_result()

    # 1. Uzun funksiyalar va murakkablik
    def check_functions(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                length = (
                    getattr(node, "end_lineno", node.lineno)
                    - node.lineno + 1
                )

                if length > 50:
                    severity = "high"
                elif length > 25:
                    severity = "medium"
                else:
                    severity = None

                if severity:
                    self.add_issue(
                        "LONG_FUNCTION", severity, node.lineno,
                        "Uzun funksiya",
                        f"{node.name} funksiyasi {length} qator.",
                        "Extract Function yordamida kichik funksiyalarga ajrating."
                    )

                complexity = 1 + sum(
                    isinstance(
                        item,
                        (
                            ast.If, ast.For, ast.AsyncFor,
                            ast.While, ast.Try, ast.BoolOp,
                            ast.IfExp, ast.ExceptHandler
                        )
                    )
                    for item in ast.walk(node)
                )

                if complexity > 15:
                    severity = "high"
                elif complexity > 8:
                    severity = "medium"
                else:
                    severity = None

                if severity:
                    self.add_issue(
                        "COMPLEXITY", severity, node.lineno,
                        "Yuqori murakkablik",
                        f"{node.name} funksiyasining taxminiy murakkabligi {complexity}.",
                        "Shartlarni soddalashtiring va vazifalarni alohida funksiyalarga ajrating."
                    )

    # 2. Katta sinflar
    def check_classes(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                length = (
                    getattr(node, "end_lineno", node.lineno)
                    - node.lineno + 1
                )

                if length > 120:
                    severity = "high"
                elif length > 80:
                    severity = "medium"
                else:
                    continue

                self.add_issue(
                    "LARGE_CLASS", severity, node.lineno,
                    "Katta sinf",
                    f"{node.name} sinfi {length} qator.",
                    "Extract Class orqali aloqasi kam vazifalarni ajrating."
                )

    # 3. Nomlash qoidalari
    def check_naming(self):
        for node in ast.walk(self.tree):

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if (
                    not node.name.startswith("__")
                    and not re.fullmatch(r"[a-z_][a-z0-9_]*", node.name)
                ):
                    self.add_issue(
                        "NAMING", "low", node.lineno,
                        "Nomlash uslubi",
                        f"{node.name} snake_case uslubiga mos emas.",
                        "Funksiya nomini snake_case shaklida yozing."
                    )

            elif isinstance(node, ast.ClassDef):
                if not re.fullmatch(r"[A-Z][a-zA-Z0-9]*", node.name):
                    self.add_issue(
                        "CLASS_NAMING", "low", node.lineno,
                        "Sinf nomlanishi",
                        f"{node.name} PascalCase uslubiga mos emas.",
                        "Sinf nomini PascalCase shaklida yozing."
                    )

    # 4. Magic Number
    def check_magic_numbers(self):
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.Constant):
                continue

            value = node.value

            if isinstance(value, bool):
                continue

            if not isinstance(value, (int, float)):
                continue

            if value in (0, 1, -1):
                continue

            self.add_issue(
                "MAGIC_NUMBER", "low", node.lineno,
                "Magic Number",
                f"{value} soni kodda izohsiz ishlatilgan bo‘lishi mumkin.",
                "Sonni mazmunli nomlangan konstantaga ajrating."
            )

    # 5. Ishlatilmagan importlar
    def check_unused_imports(self):
        used_names = {
            node.id
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Name)
            and isinstance(node.ctx, ast.Load)
        }

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]

                    if name not in used_names:
                        self.add_issue(
                            "UNUSED_IMPORT", "low", node.lineno,
                            "Ishlatilmagan import",
                            f"{name} import qilingan, ammo ishlatilmaganga o‘xshaydi.",
                            "Kerak bo‘lmasa import qatorini olib tashlang."
                        )

            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        continue

                    name = alias.asname or alias.name

                    if name not in used_names:
                        self.add_issue(
                            "UNUSED_IMPORT", "low", node.lineno,
                            "Ishlatilmagan import",
                            f"{name} import qilingan, ammo ishlatilmaganga o‘xshaydi.",
                            "Kerak bo‘lmasa import qatorini olib tashlang."
                        )

    # 6. Takrorlangan kod qatorlari
    def check_duplicate_lines(self):
        normalized = []

        for number, line in enumerate(self.lines, start=1):
            value = line.strip()

            if not value or value.startswith("#"):
                continue

            if len(value) > 15:
                normalized.append((number, value))

        counts = Counter(value for _, value in normalized)

        reported = set()

        for number, value in normalized:
            if counts[value] > 1 and value not in reported:
                reported.add(value)

                self.add_issue(
                    "DUPLICATE_CODE", "low", number,
                    "Takrorlangan kod",
                    "Ushbu kod qatori bir necha marta uchraydi.",
                    "DRY tamoyiliga amal qilib, takroriy kodni umumiy funksiyaga ajrating."
                )

    # 7. Ishlatib bo'lmaydigan kod (unreachable code)
    def check_dead_code(self):

        def inspect_body(statements):
            unreachable = False

            for statement in statements:
                if unreachable:
                    self.add_issue(
                        "DEAD_CODE", "medium",
                        statement.lineno,
                        "Dead Code",
                        "Bu kod qismiga oldingi return, raise, break yoki continue sababli yetib borilmaydi.",
                        "Ishlatilmaydigan kodni olib tashlang yoki mantiqni qayta tuzing."
                    )
                    break

                if isinstance(statement, (ast.Return, ast.Raise)):
                    unreachable = True

                elif isinstance(statement, (ast.Break, ast.Continue)):
                    unreachable = True

                # Ichki bloklarni ham tekshirish
                for child in ast.iter_child_nodes(statement):
                    if isinstance(child, (ast.If, ast.For, ast.AsyncFor,
                                          ast.While, ast.With, ast.Try)):
                        inspect_body(getattr(child, "body", []))
                        inspect_body(getattr(child, "orelse", []))
                        inspect_body(getattr(child, "finalbody", []))

        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.Module)):
                inspect_body(node.body)

    # 8. Yakuniy natija
    def make_result(self):
        unique = {}

        for issue in self.issues:
            key = (
                issue["rule"],
                issue["line"],
                issue["title"],
                issue["message"]
            )
            unique[key] = issue

        issues = sorted(
            unique.values(),
            key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x["severity"]],
                x["line"]
            )
        )

        high = sum(x["severity"] == "high" for x in issues)
        medium = sum(x["severity"] == "medium" for x in issues)
        low = sum(x["severity"] == "low" for x in issues)

        penalty = high * 15 + medium * 7 + low * 3
        score = max(0, 100 - penalty)

        return {
            "issues": issues,
            "score": score,
            "line_count": len(self.lines),
            "issue_count": len(issues),
            "high_count": high,
            "medium_count": medium,
            "low_count": low,
            "syntax_error": any(x["rule"] == "SYNTAX" for x in issues)
        }


def analyze_python(source):
    analyzer = CodeAnalyzer(source)
    return analyzer.analyze()
