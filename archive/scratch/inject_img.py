filepath = 'frontend/index.html'
content = open(filepath, 'r', encoding='utf-8').read()

target = """                <video id="cctv-video" autoplay muted playsinline
                       style="width:100%;height:100%;object-fit:cover;display:block;transition:filter 0.3s"></video>"""

replacement = """                <video id="cctv-video" autoplay muted playsinline
                       style="width:100%;height:100%;object-fit:cover;display:block;transition:filter 0.3s"></video>
                <img id="cctv-img"
                     style="width:100%;height:100%;object-fit:cover;display:none;transition:filter 0.3s">"""

if target in content:
    new_content = content.replace(target, replacement)
    open(filepath, 'w', encoding='utf-8').write(new_content)
    print("SUCCESS: cctv-img element inserted.")
else:
    print("ERROR: Target HTML block not found.")
