document.addEventListener("DOMContentLoaded", () => {
    const engine = new PureCanvasEngine();
    let balance = 1000.0;
    const betLevels = [0.10, 0.20, 0.50, 1.00, 2.00, 5.00, 10.00];
    let betIndex = 3; // 1.00
    let currentWin = 0.0;
    let isSpinning = false;

    const defaultGrid = [
        ['HIGH_LEVIATHAN', 'LOW_10', 'MID_HELMET', 'LOW_A', 'WILD_MAW'],
        ['LOW_J', 'HIGH_ANGLER', 'LOW_Q', 'MID_COMPASS', 'LOW_K'],
        ['WILD_MAW', 'LOW_A', 'HIGH_VIPER', 'LOW_10', 'HIGH_SQUID'],
        ['MID_COMPASS', 'DEAD_SEDIMENT', 'LOW_K', 'HIGH_LEVIATHAN', 'LOW_Q'],
        ['LOW_10', 'LOW_J', 'WILD_MAW', 'HIGH_ANGLER', 'LOW_A']
    ];

    function updateUI() {
        engine.updateText(engine.balMesh, `Balance: $${balance.toFixed(2)}`, 256, 64, '#000', '#fff');
        engine.updateText(engine.betMesh, `Bet: $${betLevels[betIndex].toFixed(2)}`, 128, 64, '#000', '#fff');
        engine.updateText(engine.winMesh, `Win: $${currentWin.toFixed(2)}`, 256, 64, '#000', '#ff0');
    }

    engine.onBetUp = () => {
        if (!isSpinning && betIndex < betLevels.length - 1) {
            betIndex++;
            updateUI();
        }
    };

    engine.onBetDown = () => {
        if (!isSpinning && betIndex > 0) {
            betIndex--;
            updateUI();
        }
    };

    engine.onSpin = async () => {
        if (isSpinning || balance < betLevels[betIndex]) return;
        isSpinning = true;
        currentWin = 0.0;
        balance -= betLevels[betIndex];
        updateUI();
        
        const spinStartTime = Date.now();

        try {
            const response = await fetch('/api/slot/spin', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ bet: betLevels[betIndex], feature_buy: 'NONE' })
            });
            const data = await response.json();
            
            const elapsedTime = Date.now() - spinStartTime;
            const minSpinTime = 1500;
            if (elapsedTime < minSpinTime) {
                await new Promise(r => setTimeout(r, minSpinTime - elapsedTime));
            }

            for (const event of data.events) {
                if (event.event_type === 'GRID_DROP') {
                    engine.updateGrid(event.data.grid);
                } else if (event.event_type === 'WIN_EVALUATION') {
                    currentWin += event.data.step_payout;
                    updateUI();
                    await new Promise(r => setTimeout(r, 500));
                } else if (event.event_type === 'CASCADE_DROP') {
                    await new Promise(r => setTimeout(r, 500));
                    const g = event.data.grid;
                    engine.updateGrid(g.grid ? g.grid : g);
                } else if (event.event_type === 'SPIN_COMPLETE') {
                    currentWin = event.data.total_payout || currentWin;
                    balance += currentWin;
                    updateUI();
                }
            }
        } catch (e) {
            console.error("Spin error:", e);
            engine.updateGrid(defaultGrid);
        }
        
        isSpinning = false;
    };

    engine.updateGrid(defaultGrid);
});
