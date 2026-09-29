with open("scripts/vignette_state_6_sink.js", "r") as f:
    code = f.read()

# Fix uniform linkage
code = code.replace("const uniforms = {", "mat.userData.uniforms = {")
code = code.replace("shader.uniforms.uSinkProgress = uniforms.uSinkProgress;", "shader.uniforms.uSinkProgress = mat.userData.uniforms.uSinkProgress;")
code = code.replace("shader.uniforms.uTime = uniforms.uTime;", "shader.uniforms.uTime = mat.userData.uniforms.uTime;")
code = code.replace("uniforms,", "") # remove from cells.push
code = code.replace("cell.uniforms.uTime.value = t;", "if(cell.mesh.material.userData.uniforms) cell.mesh.material.userData.uniforms.uTime.value = t;")
code = code.replace("cell.uniforms.uSinkProgress.value = progress;", "if(cell.mesh.material.userData.uniforms) cell.mesh.material.userData.uniforms.uSinkProgress.value = progress;")

with open("scripts/vignette_state_6_sink.js", "w") as f:
    f.write(code)

