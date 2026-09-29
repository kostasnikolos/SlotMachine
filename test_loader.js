const THREE = require('three');
const manager = new THREE.LoadingManager();
manager.onLoad = () => console.log('LOADED');
manager.onError = (url) => console.log('ERROR:', url);
const loader = new THREE.TextureLoader(manager);
// Try to load a fake URL
loader.load('http://localhost:9999/fake.png');
