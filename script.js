
const apiKey = "d1nr4ghr01qovv8l112gd1nr4ghr01qovv8l1130";

async function getCandles(symbol) {
    const res = await fetch(`https://finnhub.io/api/v1/stock/candle?symbol=${symbol}&resolution=D&count=20&token=${apiKey}`);
    return await res.json();
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

async function loadAll() {
    const input = document.getElementById("symbolsInput").value;
    const symbols = input.split(",").map(s => s.trim().toUpperCase());
    const results = document.getElementById("results");
    results.innerHTML = "";

    for (const symbol of symbols) {
        const div = document.createElement("div");
        div.className = "card";
        div.innerHTML = `<strong>${symbol}</strong><br><em>Lade Daten...</em>`;
        results.appendChild(div);

        try {
            const candles = await getCandles(symbol);
            if (!candles || candles.s !== "ok") {
                div.innerHTML = `<strong>${symbol}</strong><br><span style="color:red">Fehler beim Laden der Daten.</span>`;
                continue;
            }

            const closes = candles.c;
            const timestamps = candles.t.map(t => new Date(t * 1000).toLocaleDateString());
            const sma20 = calculateSMA(closes, 20);

            const currentPrice = closes[closes.length - 1];
            const currentSMA = sma20[sma20.length - 1];
            let recommendation = "🔍 Beobachten";

            if (currentPrice > currentSMA) {
                recommendation = "🟢 Tendenz positiv";
            } else if (currentPrice < currentSMA) {
                recommendation = "🔴 Tendenz negativ";
            }

            div.innerHTML = `
                <strong>${symbol}</strong><br>
                Kurs: ${currentPrice.toFixed(2)} USD<br>
                SMA(20): ${currentSMA.toFixed(2)}<br>
                <strong>Empfehlung: ${recommendation}</strong>
            `;

            const ctx = document.getElementById("chart").getContext("2d");
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: timestamps,
                    datasets: [
                        {
                            label: symbol + ' Kurs',
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
                }
            });
        } catch (error) {
            div.innerHTML = `<strong>${symbol}</strong><br><span style="color:red">Fehler beim Laden.</span>`;
        }
    }
}
