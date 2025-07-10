
const apiKey = "d1nqlrpr01qovv8kuf70d1nqlrpr01qovv8kuf7g";

async function getCandles(symbol) {
    const res = await fetch(`https://finnhub.io/api/v1/stock/candle?symbol=${symbol}&resolution=D&count=20&token=${apiKey}`);
    return await res.json();
}

async function getMomentum(symbol) {
    const res = await fetch(`https://finnhub.io/api/v1/indicator?symbol=${symbol}&resolution=D&indicator=momentum&timeperiod=10&token=${apiKey}`);
    return await res.json();
}

async function getNews(symbol) {
    const today = new Date().toISOString().split("T")[0];
    const past = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
    const res = await fetch(`https://finnhub.io/api/v1/company-news?symbol=${symbol}&from=${past}&to=${today}&token=${apiKey}`);
    const data = await res.json();
    return data.slice(0, 3);
}

function calculateSMA(values, period) {
    const sma = [];
    for (let i = period - 1; i < values.length; i++) {
        const slice = values.slice(i - period + 1, i + 1);
        const avg = slice.reduce((a, b) => a + b, 0) / period;
        sma.push(avg);
    }
    return sma;
}

async function analyze(symbol) {
    const results = document.getElementById('results');
    const box = document.createElement('div');
    box.className = 'card';
    box.innerHTML = `<strong>${symbol}</strong><br><em>Daten werden geladen...</em>`;
    results.appendChild(box);

    try {
        const candles = await getCandles(symbol);
        const momentumData = await getMomentum(symbol);
        const news = await getNews(symbol);

        const closes = candles.c;
        const timestamps = candles.t.map(t => new Date(t * 1000).toLocaleDateString());
        const sma20 = calculateSMA(closes, 20);
        const currentPrice = closes[closes.length - 1];
        const currentSMA = sma20[sma20.length - 1];
        const currentMomentum = momentumData.mom[momentumData.mom.length - 1];
        const positiveNews = news.filter(n => !n.headline.toLowerCase().includes("warn") && !n.headline.toLowerCase().includes("verlust"));

        let recommendation = "🔍 Beobachten";
        if (currentPrice > currentSMA && currentMomentum > 0 && positiveNews.length >= 2) {
            recommendation = "🟢 Kaufempfehlung";
        } else if (currentPrice < currentSMA && currentMomentum < 0) {
            recommendation = "🔴 Verkauf prüfen";
        }

        box.innerHTML = `
            <strong>${symbol}</strong><br>
            Kurs: ${currentPrice.toFixed(2)} USD<br>
            Momentum: ${currentMomentum.toFixed(2)}<br>
            SMA(20): ${currentSMA.toFixed(2)}<br>
            News-Score: ${positiveNews.length}/3 positiv<br>
            <strong>Empfehlung: ${recommendation}</strong><br>
            <canvas id="chart-${symbol}" height="150"></canvas>
        `;

        const ctx = document.getElementById(`chart-${symbol}`).getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: timestamps,
                datasets: [
                    {
                        label: 'Kurs',
                        data: closes,
                        borderColor: 'blue',
                        fill: false
                    },
                    {
                        label: 'SMA(20)',
                        data: Array(19).fill(null).concat(sma20),
                        borderColor: 'orange',
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' },
                    title: { display: true, text: `Chart für ${symbol}` }
                }
            }
        });
    } catch (e) {
        box.innerHTML = `<strong>${symbol}</strong><br><span style="color:red;">Fehler beim Laden der Daten.</span>`;
    }
}

function loadAll() {
    const input = document.getElementById('symbolsInput').value;
    const symbols = input.split(',').map(s => s.trim().toUpperCase()).filter(s => s);
    document.getElementById('results').innerHTML = '';
    symbols.forEach(symbol => analyze(symbol));
}
