import re

with open('uni_app/uni_app.py', 'r') as f:
    content = f.read()

start_marker = r"\"<path d='M138 128 H182 Q188 128 192 134 L202 184 Q176 202 160 202 Q144 202 118 184 L128 134 \""
end_marker = r"\"<ellipse cx='151' cy='209' rx='3' ry='2' fill='#ffffff' opacity='0.7'/><ellipse cx='161' cy='209' rx='3' ry='2' fill='#ffffff' opacity='0.7'/>\""

pattern = start_marker + r".*?" + end_marker

new_svg = """                # Legs
                "<rect x='148' y='180' width='8' height='30' fill='#fff3e8' stroke='#6b2e1a' stroke-width='3'/>"
                "<rect x='164' y='180' width='8' height='30' fill='#fff3e8' stroke='#6b2e1a' stroke-width='3'/>"
                # Socks
                "<rect x='146' y='196' width='12' height='10' rx='3' fill='#ffffff' stroke='#6b2e1a' stroke-width='2'/>"
                "<rect x='162' y='196' width='12' height='10' rx='3' fill='#ffffff' stroke='#6b2e1a' stroke-width='2'/>"
                # Shoes
                "<ellipse cx='152' cy='212' rx='11' ry='8' fill='#f9a8d4' stroke='#6b2e1a' stroke-width='3'/>"
                "<ellipse cx='168' cy='212' rx='11' ry='8' fill='#f9a8d4' stroke='#6b2e1a' stroke-width='3'/>"
                "<ellipse cx='148' cy='209' rx='3' ry='2' fill='#ffffff' opacity='0.7'/><ellipse cx='164' cy='209' rx='3' ry='2' fill='#ffffff' opacity='0.7'/>"
                # Skirt (drawn over the top of the legs)
                "<path d='M138 128 H182 Q188 128 192 134 L202 184 Q176 196 160 196 Q144 196 118 184 L128 134 "
                "Q132 128 138 128 Z' fill='#f9a8d4' stroke='#6b2e1a' stroke-width='3'/>"
                "<path d='M150 128 H170 L176 138 L160 150 L144 138 Z' fill='#ffffff' stroke='#6b2e1a' stroke-width='2'/>"
                "<circle cx='160' cy='142' r='2.5' fill='#b45309'/>"
                # Arms (drawn over the skirt)
                "<path d='M128 138 C140 150 148 162 154 172' fill='none' stroke='#6b2e1a' stroke-width='14' stroke-linecap='round'/>"
                "<path d='M192 138 C180 150 172 162 166 172' fill='none' stroke='#6b2e1a' stroke-width='14' stroke-linecap='round'/>"
                "<path d='M128 138 C140 150 148 162 154 172' fill='none' stroke='#fff3e8' stroke-width='10' stroke-linecap='round'/>"
                "<path d='M192 138 C180 150 172 162 166 172' fill='none' stroke='#fff3e8' stroke-width='10' stroke-linecap='round'/>"
                # Hands
                "<ellipse cx='156' cy='175' rx='6' ry='7' fill='#fff3e8' stroke='#6b2e1a' stroke-width='2'/>"
                "<ellipse cx='164' cy='175' rx='6' ry='7' fill='#fff3e8' stroke='#6b2e1a' stroke-width='2'/>" """

match = re.search(pattern, content, re.DOTALL)
if match:
    new_content = content[:match.start()] + new_svg.strip() + content[match.end():]
    with open('uni_app/uni_app.py', 'w') as f:
        f.write(new_content)
    print("Replaced successfully via regex.")
else:
    print("Pattern not found!")
