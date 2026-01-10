
let APP_DATA = null;
let CURRENT_STATE = "All";
let GEO_DATA = null;

// Debug Helper
function log(msg) {
    console.log(msg);
    let d = document.getElementById('debug-log');
    if (!d) {
        d = document.createElement('div');
        d.id = 'debug-log';
        d.style.position = 'fixed';
        d.style.bottom = '10px';
        d.style.right = '10px';
        d.style.background = 'rgba(0,0,0,0.8)';
        d.style.color = '#0f0';
        d.style.padding = '10px';
        d.style.fontSize = '12px';
        d.style.maxWidth = '300px';
        d.style.maxHeight = '200px';
        d.style.overflow = 'auto';
        d.style.zIndex = '9999';
        document.body.appendChild(d);
    }
    const line = document.createElement('div');
    line.innerText = `> ${msg}`;
    d.prepend(line);
}

const COMMON_LAYOUT = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { color: '#94a3b8' },
    margin: { t: 30, r: 20, l: 40, b: 40 },
    xaxis: { gridcolor: '#334155', showgrid: true, zeroline: false },
    yaxis: { gridcolor: '#334155', showgrid: true, zeroline: false },
    autosize: true
};

document.addEventListener('DOMContentLoaded', async () => {
    setupNavigation();
    log("Nav setup.");

    try {
        log("Fetching data...");
        const [resData, resGeo] = await Promise.all([
            fetch('data.json'),
            fetch('assets/india_states.geojson').catch(() => ({ ok: false })) // Soft fail for Geo
        ]);

        if (!resData.ok) {
            log("Data.json load failed!");
            throw new Error("Data load failed");
        }
        APP_DATA = await resData.json();
        log("Data loaded. States: " + (APP_DATA.metadata?.states?.length || 0));

        if (resGeo.ok) {
            try {
                GEO_DATA = await resGeo.json();
                log("GeoJSON loaded.");
            } catch (e) { console.warn("GeoJSON parse error", e); log("GeoJSON parse error"); }
        } else {
            log("GeoJSON fetch failed/missing.");
        }

        populateFilters();
        renderDashboard();
        log("Initial Render called.");

        // Final safeguard: Trigger a resize after 1s just in case
        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
            log("Resize triggered.");
        }, 1000);

        document.getElementById('loading').classList.add('hidden');
    } catch (e) {
        console.error(e);
        log("Error: " + e.message);
        document.getElementById('loading').innerHTML = `<div style="color:red">Failed to load data. <br> ${e.message}</div>`;
    }
});

function setupNavigation() {
    document.querySelectorAll('.nav-item').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

            e.target.classList.add('active');
            const targetId = e.target.getAttribute('data-tab');
            document.getElementById(targetId).classList.add('active');

            // Force resize for Plotly
            setTimeout(() => {
                const pane = document.getElementById(targetId);
                const plots = pane.querySelectorAll('.js-plotly-plot');
                plots.forEach(p => Plotly.Plots.resize(p));
                window.dispatchEvent(new Event('resize'));
            }, 50);
        });
    });

    document.getElementById('state-filter').addEventListener('change', (e) => {
        CURRENT_STATE = e.target.value;
        renderDashboard();
    });
}

function populateFilters() {
    const selector = document.getElementById('state-filter');
    selector.innerHTML = '<option value="All">All India</option>';
    if (APP_DATA && APP_DATA.metadata && APP_DATA.metadata.states) {
        APP_DATA.metadata.states.forEach(st => {
            if (st === 'All') return;
            const opt = document.createElement('option');
            opt.value = st;
            opt.innerText = st;
            selector.appendChild(opt);
        });
    }
}

function renderDashboard() {
    if (!APP_DATA) return;
    const stats = APP_DATA.stats[CURRENT_STATE] || APP_DATA.stats['All'];
    log(`Render State: ${CURRENT_STATE}. Keys: ${Object.keys(stats).join(', ')}`);

    // Header
    const subtitle = document.getElementById('page-subtitle');
    if (subtitle) subtitle.innerText = `Analytics for Region: ${CURRENT_STATE}`;

    // Render Components with safeguards
    safeRun(() => renderKPIs(stats.kpis), "KPIs");
    safeRun(() => renderAI(stats.ai), "AI");

    // Overview Charts - Global
    if (CURRENT_STATE === 'All') {
        if (APP_DATA.stats.All.state_performance) {
            safeRun(() => plotStateBar(APP_DATA.stats.All.state_performance), "StateBar");
        }
        if (APP_DATA.stats.All.map_data) {
            safeRun(() => plotMap(APP_DATA.stats.All.map_data), "Map");
        } else {
            log("No map_data found in stats.All");
        }
    } else {
        try { Plotly.purge('chart-state-bar'); } catch { }
        try { Plotly.purge('chart-map'); } catch { }
    }

    if (APP_DATA.stats.All.treemap) {
        safeRun(() => plotTreemap(APP_DATA.stats.All.treemap), "Treemap");
    }

    // Tabbed Charts (Render all, CSS hides them)
    safeRun(() => plotTrends(stats), "Trends");

    if (stats.age_distribution) {
        safeRun(() => plotAgePie(stats.age_distribution), "AgePie");
    }

    if (stats.forecast_enrolment) {
        safeRun(() => plotForecast(stats.forecast_enrolment), "Forecast");
    } else {
        log("No forecast_enrolment data");
        const el = document.getElementById('chart-forecast');
        if (el) el.innerHTML = "<div style='padding:20px; color:#666'>Forecast available only for National View</div>";
    }

    safeRun(() => renderRecsTable(APP_DATA.stats.All.recommendations), "Recs");
}

function safeRun(fn, name) {
    try {
        fn();
    } catch (e) {
        console.error(`Error rendering ${name}:`, e);
        log(`ERR ${name}: ${e.message}`);
    }
}

function renderKPIs(kpis) {
    if (!kpis) return;
    const fmt = n => new Intl.NumberFormat('en-IN').format(n);
    const updates = (kpis.total_demo_updates || 0) + (kpis.total_bio_updates || 0);
    const enr = kpis.total_enrolments || 1;
    const intensity = ((updates / enr) * 100).toFixed(1);

    setText('kpi-enrolments', fmt(kpis.total_enrolments || 0));
    setText('kpi-demo-updates', fmt(kpis.total_demo_updates || 0));
    setText('kpi-bio-updates', fmt(kpis.total_bio_updates || 0));
    setText('kpi-intensity', intensity + "%");

    const data = [{
        domain: { x: [0, 1], y: [0, 1] },
        value: parseFloat(intensity),
        title: { text: "Saturation" },
        type: "indicator",
        mode: "gauge+number",
        gauge: {
            axis: { range: [0, 100] },
            bar: { color: "#3b82f6" },
            bgcolor: "#1e293b",
            borderwidth: 2,
            bordercolor: "#334155"
        }
    }];
    Plotly.newPlot('gauge-container', data, { ...COMMON_LAYOUT, width: 150, height: 100, margin: { t: 0, b: 0 } }, { displayModeBar: false });
}

function renderAI(ai) {
    const box = document.getElementById('ai-insight-box');
    const badge = document.getElementById('ai-status');
    const text = document.getElementById('ai-text-content');
    const policy = document.getElementById('ai-policy-text');

    if (ai && ai.kpi_summary) {
        if (box) box.classList.remove('hidden');
        if (badge) badge.classList.remove('hidden');
        if (text) text.innerHTML = ai.kpi_summary.replace(/\n/g, '<br>');
        if (policy && ai.policy_draft) policy.innerText = ai.policy_draft;
    } else {
        if (box) box.classList.add('hidden');
        if (badge) badge.classList.add('hidden');
    }
}

function plotStateBar(data) {
    const trace = {
        x: data.map(d => d.Total),
        y: data.map(d => d.state),
        type: 'bar',
        orientation: 'h',
        marker: { color: '#3b82f6' }
    };
    Plotly.newPlot('chart-state-bar', [trace], { ...COMMON_LAYOUT, margin: { t: 0, l: 100, b: 30, r: 10 }, yaxis: { automargin: true } }, { responsive: true });
}

function plotMap(data) {
    // If we have GeoJSON, render a Choropleth
    if (GEO_DATA) {
        const trace = {
            type: 'choropleth',
            geojson: GEO_DATA,
            locations: data.map(d => d.state),
            z: data.map(d => d.Total_Enr),
            featureidkey: 'properties.ST_NM', // Common key for Indian states
            colorscale: 'Blues',
            marker: { line: { color: '#334155', width: 0.5 } }
        };
        const layout = {
            ...COMMON_LAYOUT,
            geo: {
                fitbounds: "locations",
                visible: false,
                bgcolor: 'rgba(0,0,0,0)'
            }
        };
        Plotly.newPlot('chart-map', [trace], layout, { responsive: true });
        return;
    }

    // Fallback: Horizontal Bar if no GeoJSON
    // Use the same data but show it as a bar chart if map fails
    document.getElementById('chart-map').innerHTML = "<div style='padding:40px; text-align:center; color:#64748b'>GeoJSON Loaded Failed. Switch to Bar View.</div>";
}

function plotTreemap(data) {
    if (!data || data.length === 0) return;
    const labels = data.map(d => (d.district || d.state) + " (" + d.state + ")");
    const parents = data.map(() => "");
    const values = data.map(d => d.Total);

    const trace = {
        type: "treemap",
        labels: labels,
        parents: parents,
        values: values,
        textinfo: "label+value",
        marker: { colorscale: 'Deep' }
    };
    Plotly.newPlot('chart-treemap', [trace], { ...COMMON_LAYOUT }, { responsive: true });
}

function plotTrends(stats) {
    // Enrolment
    if (stats.trend_enrolment && stats.trend_enrolment.length > 0) {
        log(`Plotting Enr Trend: ${stats.trend_enrolment.length} pts`);
        const keys = Object.keys(stats.trend_enrolment[0]).filter(k => k !== 'date');
        log(`Enr Keys: ${keys.join(', ')}`);

        // Force height
        document.getElementById('chart-trend-enr').style.height = '400px';

        const traces = keys.map(k => ({
            x: stats.trend_enrolment.map(d => d.date),
            y: stats.trend_enrolment.map(d => d[k]),
            name: k.replace(/_/g, ' '),
            type: 'scatter',
            mode: 'lines+markers',
            stackgroup: 'one'
        }));
        Plotly.newPlot('chart-trend-enr', traces, { ...COMMON_LAYOUT, title: 'Enrolment' }, { responsive: true });
    } else {
        log("Skip Enr Trend: No Data/Empty");
    }

    // Demo
    if (stats.trend_demo && stats.trend_demo.length > 0) {
        log(`Plotting Demo Trend: ${stats.trend_demo.length} pts`);
        const keys = Object.keys(stats.trend_demo[0]).filter(k => k !== 'date');
        const traces = keys.map(k => ({
            x: stats.trend_demo.map(d => d.date),
            y: stats.trend_demo.map(d => d[k]),
            name: k.replace(/_/g, ' '),
            type: 'scatter',
            mode: 'lines+markers'
        }));
        Plotly.newPlot('chart-trend-demo', traces, COMMON_LAYOUT, { responsive: true });
    } else { log("Skip Demo Trend"); }

    // Bio
    if (stats.trend_bio && stats.trend_bio.length > 0) {
        log(`Plotting Bio Trend: ${stats.trend_bio.length} pts`);
        const keys = Object.keys(stats.trend_bio[0]).filter(k => k !== 'date');
        const traces = keys.map(k => ({
            x: stats.trend_bio.map(d => d.date),
            y: stats.trend_bio.map(d => d[k]),
            name: k.replace(/_/g, ' '),
            type: 'bar'
        }));
        Plotly.newPlot('chart-trend-bio', traces, { ...COMMON_LAYOUT, barmode: 'stack' }, { responsive: true });
    } else { log("Skip Bio Trend"); }
}

function plotAgePie(dist) {
    if (!dist) return;
    const trace = {
        labels: Object.keys(dist),
        values: Object.values(dist),
        type: 'pie',
        hole: 0.4,
        marker: { colors: ['#3b82f6', '#10b981', '#f59e0b'] }
    };
    Plotly.newPlot('chart-age-pie', [trace], { ...COMMON_LAYOUT, showlegend: true }, { responsive: true });

    // Funnel
    const entries = Object.entries(dist).sort((a, b) => b[1] - a[1]);
    const traceFunnel = {
        y: entries.map(x => x[0]),
        x: entries.map(x => x[1]),
        type: 'funnel',
        marker: { color: ['#3b82f6', '#10b981', '#f59e0b'] }
    };
    Plotly.newPlot('chart-funnel', [traceFunnel], { ...COMMON_LAYOUT, margin: { l: 150 } }, { responsive: true });
}

function plotForecast(data) {
    if (!data) return;
    const trace = {
        x: data.map(d => d.date),
        y: data.map(d => d.forecast),
        type: 'scatter',
        mode: 'lines+markers',
        line: { dash: 'dot', width: 3, color: '#f59e0b' },
        name: 'Forecast'
    };
    Plotly.newPlot('chart-forecast', [trace], { ...COMMON_LAYOUT }, { responsive: true });
}

function renderRecsTable(list) {
    const tbody = document.querySelector('#recs-table tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    if (!list) return;

    list.slice(0, 15).forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.State || item.state || 'N/A'}</td>
            <td>${item.District || item.district || 'N/A'}</td>
            <td>${item.Issue || item.metric || 'N/A'}</td>
            <td><span style="color: #fca5a5">${item.Action || item.action || 'Check'}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.innerText = val;
}
