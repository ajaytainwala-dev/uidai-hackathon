
// State
let rawData = {
    enrolment: [],
    demographic: [],
    biometric: []
};
let allStates = [];

// DOM Elements
const els = {
    kpiEnr: document.getElementById('kpi-enr'),
    kpiDemo: document.getElementById('kpi-demo'),
    kpiBio: document.getElementById('kpi-bio'),
    stateSelect: document.getElementById('stateFilter'),
    status: document.getElementById('status'),
    recordCount: document.getElementById('recordCount')
};

// Config
const DATA_ROOT = '../data/';
const DATA_TYPES = {
    'enrolment': 'api_data_aadhar_enrolment',
    'demographic': 'api_data_aadhar_demographic',
    'biometric': 'api_data_aadhar_biometric'
};

async function init() {
    try {
        els.status.textContent = "Loading Manifest...";
        const manifest = await fetch('manifest.json').then(r => r.json());

        // Load Data Parallel
        els.status.textContent = "Fetching Data...";
        const promises = [];

        for (const [key, folder] of Object.entries(DATA_TYPES)) {
            if (manifest[folder]) {
                for (const file of manifest[folder]) {
                    promises.push(loadCSV(key, `${DATA_ROOT}${folder}/${file}`));
                }
            }
        }

        await Promise.all(promises);

        els.status.textContent = "Processing...";
        processData();

        els.status.textContent = "Ready";
        renderDashboard();

    } catch (e) {
        console.error(e);
        els.status.textContent = "Error: " + e.message;
    }
}

function loadCSV(type, url) {
    return new Promise((resolve, reject) => {
        Papa.parse(url, {
            download: true,
            header: true,
            skipEmptyLines: true,
            dynamicTyping: true,
            complete: function (results) {
                rawData[type] = rawData[type].concat(results.data);
                resolve();
            },
            error: function (err) {
                console.error("CSV Error", err);
                resolve(); // resolve anyway to continue
            }
        });
    });
}

function processData() {
    // Extract States for Filter
    const states = new Set();

    // We only scan Enrolment for states to be fast, or scan all if needed
    rawData.enrolment.forEach(r => { if (r.state) states.add(r.state); });

    // Check others if enrolled is empty (fallback)
    if (states.size === 0) {
        rawData.demographic.forEach(r => { if (r.state) states.add(r.state); });
    }

    allStates = Array.from(states).sort();

    // Populate Dropdown
    allStates.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        els.stateSelect.appendChild(opt);
    });

    els.stateSelect.addEventListener('change', renderDashboard);

    // Update Debug Info
    const totalRows = rawData.enrolment.length + rawData.demographic.length + rawData.biometric.length;
    els.recordCount.textContent = `Rows: ${totalRows.toLocaleString()}`;
}

function getFilteredData() {
    const selectedState = els.stateSelect.value;
    if (selectedState === 'All') {
        return rawData;
    }

    return {
        enrolment: rawData.enrolment.filter(r => r.state === selectedState),
        demographic: rawData.demographic.filter(r => r.state === selectedState),
        biometric: rawData.biometric.filter(r => r.state === selectedState)
    };
}

function renderDashboard() {
    const data = getFilteredData();

    // 1. KPIs
    const totalEnr = _.sumBy(data.enrolment, r => (r.age_0_5 || 0) + (r.age_5_17 || 0) + (r.age_18_greater || 0));
    const totalDemo = _.sumBy(data.demographic, r => (r.demo_age_5_17 || 0) + (r.demo_age_18_plus || 0)); // Note: check variable names from CSV
    // Check demo CSV headers: often 'demo_age_17_' -> need to handle loose matching or standardized
    // Constants say: COL_DEMO_AGE_18_PLUS = 'demo_age_17_' 

    // Let's safe sum using a helper to handle exact CSV column names
    const sumDemo = _.sumBy(data.demographic, r => (r['demo_age_5_17'] || 0) + (r['demo_age_17_'] || 0));
    const sumBio = _.sumBy(data.biometric, r => (r['bio_age_5_17'] || 0) + (r['bio_age_17_'] || 0));

    els.kpiEnr.textContent = totalEnr.toLocaleString();
    els.kpiDemo.textContent = sumDemo.toLocaleString();
    els.kpiBio.textContent = sumBio.toLocaleString();

    // 2. Gauge Chart
    const totalUpdates = sumDemo + sumBio;
    const saturation = totalEnr > 0 ? (totalUpdates / totalEnr) * 100 : 0;

    Plotly.newPlot('gaugeChart', [{
        type: "indicator",
        mode: "gauge+number",
        value: saturation,
        title: { text: "Saturation %", font: { size: 14 } },
        gauge: { axis: { range: [0, 100] } }
    }], { margin: { t: 0, b: 0, l: 30, r: 30 }, height: 250 });

    // 3. Bar Chart (Top States) - Only if All, or just District if State selected
    if (els.stateSelect.value === 'All') {
        const stateGroups = _.groupBy(data.enrolment, 'state');
        const stateAgg = Object.keys(stateGroups).map(k => {
            return {
                state: k,
                total: _.sumBy(stateGroups[k], r => (r.age_0_5 || 0) + (r.age_5_17 || 0) + (r.age_18_greater || 0))
            };
        }).sort((a, b) => b.total - a.total).slice(0, 10);

        Plotly.newPlot('barChartState', [{
            x: stateAgg.map(x => x.state),
            y: stateAgg.map(x => x.total),
            type: 'bar',
            marker: { color: '#0068c9' }
        }], { title: "Top 10 States", margin: { t: 30, l: 40, r: 10, b: 80 } });
    } else {
        // District View
        const distGroups = _.groupBy(data.enrolment, 'district');
        const distAgg = Object.keys(distGroups).map(k => {
            return {
                district: k,
                total: _.sumBy(distGroups[k], r => (r.age_0_5 || 0) + (r.age_5_17 || 0) + (r.age_18_greater || 0))
            };
        }).sort((a, b) => b.total - a.total).slice(0, 10);

        Plotly.newPlot('barChartState', [{
            x: distAgg.map(x => x.district),
            y: distAgg.map(x => x.total),
            type: 'bar',
            marker: { color: '#0068c9' }
        }], { title: "Top 10 Districts", margin: { t: 30, l: 40, r: 10, b: 80 } });
    }

    // 4. Treemap
    // We limit to top 500 records for performance if raw
    // For treemap we need hierarchy: State -> District
    const treemapData = [];
    // We aggregate by State, District
    const treeMapObj = {};
    data.enrolment.forEach(r => {
        const key = `${r.state}|${r.district}`;
        if (!treeMapObj[key]) treeMapObj[key] = 0;
        treeMapObj[key] += (r.age_0_5 || 0) + (r.age_5_17 || 0) + (r.age_18_greater || 0);
    });

    const treeParents = [];
    const treeLabels = [];
    const treeValues = [];

    // Root
    treeLabels.push("India");
    treeParents.push("");
    treeValues.push(0); // Plotly sum calculates this

    const stateSet = new Set();

    Object.entries(treeMapObj).forEach(([key, val]) => {
        const [st, dist] = key.split('|');
        if (!stateSet.has(st)) {
            treeLabels.push(st);
            treeParents.push("India");
            treeValues.push(0);
            stateSet.add(st);
        }
        treeLabels.push(dist + " (" + st + ")"); // Unique Label
        treeParents.push(st);
        treeValues.push(val);
    });

    Plotly.newPlot('treemapChart', [{
        type: "treemap",
        labels: treeLabels,
        parents: treeParents,
        values: treeValues,
        textinfo: "label+value"
    }], { margin: { t: 0, l: 0, r: 0, b: 0 } });

    // 5. Enrolment Tab Charts
    // Pie
    const pieData = [
        _.sumBy(data.enrolment, 'age_0_5'),
        _.sumBy(data.enrolment, 'age_5_17'),
        _.sumBy(data.enrolment, 'age_18_greater')
    ];

    Plotly.newPlot('pieAge', [{
        values: pieData,
        labels: ['0-5', '5-17', '18+'],
        type: 'pie',
        hole: 0.4
    }], { height: 300, margin: { t: 0, b: 0, l: 0, r: 0 } });

    // Trend
    // Group by Date
    const trendObj = {};
    data.enrolment.forEach(r => {
        if (!r.date) return;
        if (!trendObj[r.date]) trendObj[r.date] = { a: 0, b: 0, c: 0 };
        trendObj[r.date].a += r.age_0_5 || 0;
        trendObj[r.date].b += r.age_5_17 || 0;
        trendObj[r.date].c += r.age_18_greater || 0;
    });

    // Sort dates
    const dates = Object.keys(trendObj).sort((a, b) => new Date(a.split('-').reverse().join('-')) - new Date(b.split('-').reverse().join('-')));

    Plotly.newPlot('trendChart', [
        { x: dates, y: dates.map(d => trendObj[d].a), name: '0-5', type: 'scatter' },
        { x: dates, y: dates.map(d => trendObj[d].b), name: '5-17', type: 'scatter' },
        { x: dates, y: dates.map(d => trendObj[d].c), name: '18+', type: 'scatter' }
    ], { title: "Enrolment Trend", margin: { t: 40 } });

}

// UI Helpers
function showTab(id) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));

    document.getElementById(id).classList.add('active');
    // Find button
    event.target.classList.add('active');

    // Resize plots
    window.dispatchEvent(new Event('resize'));
}

// Start
init();
