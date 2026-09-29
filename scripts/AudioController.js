class AudioController {
    constructor() {
        this.context = null;
        this.buffers = {
            breath: null,
            chain: null,
            spank: null
        };
        this.activeNodes = {
            breath: null,
            breathGain: null
        };
        this.isInitialized = false;
        this.basePath = '/slot_engine/static/assets/audio/';
    }

    async init() {
        if (this.isInitialized) return;
        
        // Initialize AudioContext synchronously!
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        this.context = new AudioContext();

        // Resume synchronously! Safari requires this in the same tick as the click event
        if (this.context.state === 'suspended') {
            this.context.resume();
        }

        await this.loadAssets();
        this.isInitialized = true;
    }

    async loadAssets() {
        const assets = [
            { name: 'breath', url: 'breath.wav' },
            { name: 'chain', url: 'chain.wav' },
            { name: 'spank', url: 'spank.wav' }
        ];

        const loadPromises = assets.map(async (asset) => {
            try {
                const response = await fetch(`${this.basePath}${asset.url}`);
                const arrayBuffer = await response.arrayBuffer();
                const audioBuffer = await this.context.decodeAudioData(arrayBuffer);
                this.buffers[asset.name] = audioBuffer;
            } catch (error) {
                console.error(`Error loading audio asset ${asset.name}:`, error);
            }
        });

        await Promise.all(loadPromises);
    }

    playBreath(loop = true) {
        if (!this.context || !this.buffers.breath) return;

        this.stopBreath();

        const source = this.context.createBufferSource();
        source.buffer = this.buffers.breath;
        source.loop = loop;

        const gainNode = this.context.createGain();
        gainNode.gain.value = 0.3;

        source.connect(gainNode);
        gainNode.connect(this.context.destination);

        source.start(0);

        this.activeNodes.breath = source;
        this.activeNodes.breathGain = gainNode;
    }

    stopBreath() {
        if (this.activeNodes.breath && this.activeNodes.breathGain) {
            const gainNode = this.activeNodes.breathGain;
            const source = this.activeNodes.breath;
            
            gainNode.gain.setValueAtTime(gainNode.gain.value, this.context.currentTime);
            gainNode.gain.linearRampToValueAtTime(0, this.context.currentTime + 1.0);
            
            source.stop(this.context.currentTime + 1.0);
            
            this.activeNodes.breath = null;
            this.activeNodes.breathGain = null;
        }
    }

    playChain() {
        if (!this.context || !this.buffers.chain) return;

        const source = this.context.createBufferSource();
        source.buffer = this.buffers.chain;
        
        const gainNode = this.context.createGain();
        gainNode.gain.value = 0.8;

        source.connect(gainNode);
        gainNode.connect(this.context.destination);

        source.start(0);
    }

    playSpank() {
        if (!this.context || !this.buffers.spank) return;

        const source = this.context.createBufferSource();
        source.buffer = this.buffers.spank;

        const gainNode = this.context.createGain();
        gainNode.gain.value = 1.0; 

        source.connect(gainNode);
        gainNode.connect(this.context.destination);

        source.start(0);
    }
}

export default AudioController;
