import glob, re, json

colors = {}
spacings = {}
radii = {}
custom_styles = []

for f in sorted(glob.glob('scratch/stitch_extracted/*/*.html')):
    text = open(f, encoding='utf-8', errors='ignore').read()
    # Find colors
    m = re.search(r'"colors":\s*({[^{}]*(?:{[^{}]*}[^{}]*)*})', text)
    if m:
        try:
            c = json.loads(m.group(1))
            colors.update(c)
        except Exception as e:
            pass
    # Find spacing
    m2 = re.search(r'"spacing":\s*({[^{}]*})', text)
    if m2:
        try:
            s = json.loads(m2.group(1))
            spacings.update(s)
        except Exception as e:
            pass
    # Find borderRadius
    m3 = re.search(r'"borderRadius":\s*({[^{}]*})', text)
    if m3:
        try:
            r = json.loads(m3.group(1))
            radii.update(r)
        except Exception as e:
            pass
    # Find style blocks
    styles = re.findall(r'<style>(.*?)</style>', text, re.DOTALL)
    for st in styles:
        if st.strip() not in custom_styles:
            custom_styles.append(st.strip())

print("=== COLORS ===")
for k, v in sorted(colors.items()):
    if isinstance(v, str):
        print(f"  --color-{k}: {v};")

print("\n=== SPACING ===")
for k, v in sorted(spacings.items()):
    print(f"  --spacing-{k}: {v};")

print("\n=== BORDER RADIUS ===")
for k, v in sorted(radii.items()):
    print(f"  --radius-{k.lower()}: {v};")

print("\n=== CUSTOM STYLES ===")
for st in custom_styles:
    print(st)
