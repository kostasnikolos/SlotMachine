import re

with open("slot_engine/static/js/WebGLGameEngine.js", "r") as f:
    code = f.read()

replacement = """
    onWindowResize() {
        if (!this.canvas || !this.canvas.parentElement) return;
        
        // Force the parent to evaluate its actual size, or fallback to known good mobile dimensions
        let width = this.canvas.parentElement.clientWidth || 390;
        let height = this.canvas.parentElement.clientHeight || 480;
        
        // If height is unusually small (CSS hasn't loaded), force it to 480
        if (height < 200) height = 480;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        // Use window.innerWidth to determine if we are on mobile reliably
        if (window.innerWidth <= 600) {
            this.camera.position.z = 100; // Fixed reliable Z for mobile
        } else {
            this.camera.position.z = 72; // Desktop
        }

        this.renderer.setSize(width, height);
"""

code = re.sub(r'    onWindowResize\(\) \{.*?this\.renderer\.setSize\(width, height\);', replacement, code, flags=re.DOTALL)

with open("slot_engine/static/js/WebGLGameEngine.js", "w") as f:
    f.write(code)

