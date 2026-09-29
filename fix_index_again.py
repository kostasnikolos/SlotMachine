import re

with open("slot_engine/static/index.html", "r") as f:
    code = f.read()

code = code.replace('href="./style.css"', 'href="/static/style.css"')
code = code.replace('src="./js/WebGLGameEngine.js"', 'src="/static/js/WebGLGameEngine.js"')
code = code.replace('src="./js/monolithic_frame.js', 'src="/static/js/monolithic_frame.js')
code = code.replace('src="./js/webgl_reel_engine.js', 'src="/static/js/webgl_reel_engine.js')
code = code.replace('src="./js/leviathan_director.js', 'src="/static/js/leviathan_director.js')
code = code.replace('src="./sound.js', 'src="/static/sound.js')
code = code.replace('src="./game.js', 'src="/static/game.js')

with open("slot_engine/static/index.html", "w") as f:
    f.write(code)

