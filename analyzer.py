import ast, re
from collections import Counter

def analyze_python(source):
    issues=[]
    lines=source.splitlines()
    def add(rule, severity, line, title, message, suggestion):
        issues.append(dict(rule=rule,severity=severity,line=line or 1,title=title,message=message,suggestion=suggestion))
    try:
        tree=ast.parse(source)
    except SyntaxError as e:
        add("SYNTAX","high",e.lineno,"Sintaksis xatosi",e.msg,"Python sintaksisini tekshirib, xatoni tuzating.")
        return result(issues,len(lines))
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            length=getattr(node,"end_lineno",node.lineno)-node.lineno+1
            if length>30:
                add("LONG_FUNCTION","medium",node.lineno,"Uzun funksiya",f"{node.name} funksiyasi {length} qator.","Extract Function: kichik funksiyalarga ajrating.")
            if not re.fullmatch(r"[a-z_][a-z0-9_]*",node.name):
                add("NAMING","low",node.lineno,"Nomlash uslubi",f"{node.name} snake_case uslubiga mos emas.","Funksiya nomini snake_case ko‘rinishida yozing.")
            complexity=1+sum(isinstance(n,(ast.If,ast.For,ast.While,ast.Try,ast.BoolOp,ast.IfExp,ast.ExceptHandler)) for n in ast.walk(node))
            if complexity>10:
                add("COMPLEXITY","medium",node.lineno,"Yuqori murakkablik",f"{node.name} funksiyasining taxminiy murakkabligi {complexity}.","Shartlarni soddalashtiring va vazifalarni ajrating.")
        if isinstance(node,ast.ClassDef):
            length=getattr(node,"end_lineno",node.lineno)-node.lineno+1
            if length>100:
                add("LARGE_CLASS","medium",node.lineno,"Katta sinf",f"{node.name} sinfi {length} qator.","Extract Class yordamida vazifalarni alohida sinflarga ajrating.")
        if isinstance(node,ast.Constant) and isinstance(node.value,(int,float)) and node.value not in (0,1,-1):
            add("MAGIC_NUMBER","low",getattr(node,"lineno",1),"Magic Number",f"{node.value} soni kodda izohsiz ishlatilgan bo‘lishi mumkin.","Sonni mazmunli nomlangan konstantaga ajrating.")
    normalized=[(i,re.sub(r"\s+"," ",x.strip())) for i,x in enumerate(lines,1) if x.strip() and not x.strip().startswith("#")]
    counts=Counter(v for _,v in normalized if len(v)>12)
    repeated={v for v,n in counts.items() if n>1}
    seen=set()
    for line,v in normalized:
        if v in repeated and v not in seen:
            seen.add(v); add("DUPLICATE","low",line,"Takrorlangan kod","O‘xshash kod qatori bir necha marta uchraydi.","DRY: takroriy mantiqni umumiy funksiyaga ajrating.")
    imports=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imports += [(a.asname or a.name.split(".")[0],node.lineno) for a in node.names]
        elif isinstance(node,ast.ImportFrom):
            imports += [(a.asname or a.name,node.lineno) for a in node.names]
    for name,line in imports:
        if len(re.findall(r"\b"+re.escape(name)+r"\b",source))<=1:
            add("UNUSED_IMPORT","low",line,"Ishlatilmagan import",f"{name} import qilingan, ammo ishlatilmaganga o‘xshaydi.","Kerak bo‘lmasa importni olib tashlang.")
    unique={}
    for x in issues: unique[(x["rule"],x["line"],x["title"])]=x
    return result(list(unique.values()),len(lines))

def result(issues,line_count):
    penalty=sum({"high":15,"medium":7,"low":3}[x["severity"]] for x in issues)
    return {"issues":sorted(issues,key=lambda x:({"high":0,"medium":1,"low":2}[x["severity"]],x["line"])),
            "score":max(0,100-penalty),"line_count":line_count,"issue_count":len(issues),
            "high_count":sum(x["severity"]=="high" for x in issues),
            "medium_count":sum(x["severity"]=="medium" for x in issues),
            "low_count":sum(x["severity"]=="low" for x in issues)}
