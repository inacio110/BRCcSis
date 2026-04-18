import re

with open("src/static/index.html", "r") as f:
    content = f.read()

# Encontrar todas as tags script sem src
pattern = re.compile(r"<script>\s*(.*?)\s*</script>", re.DOTALL)
matches = list(pattern.finditer(content))

print(f"Found {len(matches)} inline scripts.")

all_js = []
for i, m in enumerate(matches):
    all_js.append(f"// ==================== INLINE SCRIPT {i} ====================")
    all_js.append(m.group(1))

# Salvar o JS extraido
with open("src/static/js/app_inline.js", "w") as f:
    f.write("\n".join(all_js))

# Substituir no HTML
new_content = content
# Substituímos a primeira ocorrencia pela tag com src
first_match = matches[0]
new_content = new_content[:first_match.start()] + '<script src="js/app_inline.js"></script>' + new_content[first_match.end():]

# Removemos os outros
for m in reversed(matches[1:]):
    # Encontramos novamente no new_content? Não, usar indices seria ruim com substituição string simples.
    pass

# Uma abordagem melhor:
def replacer(match):
    global replaced_first
    if not replaced_first:
        replaced_first = True
        return '<script src="js/app_inline.js"></script>'
    return ''

replaced_first = False
new_content = pattern.sub(replacer, content)

with open("src/static/index.html", "w") as f:
    f.write(new_content)

print("Done. Saved inline scripts to src/static/js/app_inline.js and updated index.html")
