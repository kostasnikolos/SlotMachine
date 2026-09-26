// ============================================================================
// GLSL Screen-Space Fluid Refraction & Chromatic Aberration Shader
// Reusable template for high-impact underwater / shockwave distortion
// ============================================================================

uniform sampler2D tDiffuse;       // Scene render texture
uniform sampler2D tNormal;        // Water caustic / disturbance normal map
uniform vec2 uResolution;         // Viewport resolution
uniform float uTime;              // Elapsed time
uniform vec2 uShockCenter;        // Center of explosion / bite (UV coords 0..1)
uniform float uShockRadius;       // Shockwave radius
uniform float uShockStrength;     // Shockwave intensity
uniform float uChromaticSplit;    // RGB separation magnitude

varying vec2 vUv;

void main() {
    vec2 uv = vUv;
    
    // 1. Water Caustics Subtle Continuous Refraction
    vec2 normalCoord = uv * 2.5 + vec2(uTime * 0.04, uTime * 0.02);
    vec4 normalTex = texture2D(tNormal, normalCoord);
    vec2 waterOffset = (normalTex.rg - 0.5) * 0.015;
    
    // 2. Radial Shockwave Displacement
    vec2 dir = uv - uShockCenter;
    float dist = length(dir);
    vec2 shockOffset = vec2(0.0);
    
    if (dist < uShockRadius && dist > uShockRadius - 0.15) {
        float wave = sin((dist - uShockRadius) * 20.0);
        shockOffset = normalize(dir) * wave * uShockStrength;
    }
    
    vec2 finalUv = uv + waterOffset + shockOffset;
    
    // 3. Chromatic Aberration Lens Split (RGB Channel Separation)
    vec2 rOffset = finalUv + vec2(uChromaticSplit, 0.0);
    vec2 gOffset = finalUv;
    vec2 bOffset = finalUv - vec2(uChromaticSplit, 0.0);
    
    float r = texture2D(tDiffuse, rOffset).r;
    float g = texture2D(tDiffuse, gOffset).g;
    float b = texture2D(tDiffuse, bOffset).b;
    
    // 4. Subtle Deep Sea Vignette
    float vignette = 1.0 - smoothstep(0.4, 0.95, length(uv - 0.5));
    
    gl_FragColor = vec4(vec3(r, g, b) * vignette, 1.0);
}
