/* ==========================================================================
   AgroEdge AI — script.js
   Dummy-data phase: everything here runs client-side with simulated values.
   Each section marked with "FLASK HOOK" is where a fetch() to localhost
   will replace the simulation once the backend is connected (Step 6 of
   the build plan). The DOM ids/classes below match index.html + style.css.
   ========================================================================== */

(() => {
  'use strict';

  /* ------------------------------------------------------------------ */
  /* State                                                              */
  /* ------------------------------------------------------------------ */

  const state = {
    powerSaving: false,
    refreshMs: 1000,
    timerId: null,
    chartWindow: 12,          // points kept on screen per chart
    sensors: {
      temperature:  { value: 34,  min: 18, max: 42, unit: '°C' },
      humidity:     { value: 68,  min: 30, max: 90, unit: '%'  },
      soilMoisture: { value: 41,  min: 10, max: 80, unit: '%'  },
      light:        { value: 720, min: 100, max: 1200, unit: 'Lux' },
      wind:         { value: 8,   min: 0,  max: 30, unit: 'km/h' },
      battery:      { value: 92,  min: 0,  max: 100, unit: '%'  }
    }
  };

  const charts = {};

  /* ------------------------------------------------------------------ */
  /* Utilities                                                          */
  /* ------------------------------------------------------------------ */

  const $ = (id) => document.getElementById(id);

  function clamp(v, min, max) {
    return Math.max(min, Math.min(max, v));
  }

  // Small random walk so values drift instead of jumping around.
  function drift(value, min, max, step) {
    const delta = (Math.random() - 0.5) * step;
    return Math.round(clamp(value + delta, min, max) * 10) / 10;
  }

  function trendArrow(oldVal, newVal) {
    if (newVal > oldVal) return { symbol: '▲', cls: 'trend-up' };
    if (newVal < oldVal) return { symbol: '▼', cls: 'trend-down' };
    return { symbol: '▬', cls: 'trend-flat' };
  }

  function setTrend(el, oldVal, newVal) {
    if (!el) return;
    const t = trendArrow(oldVal, newVal);
    el.textContent = t.symbol;
    el.classList.remove('trend-up', 'trend-down', 'trend-flat');
    el.classList.add(t.cls);
  }

  function formatClock(date) {
    return date.toLocaleTimeString('en-GB', { hour12: false });
  }

  /* ------------------------------------------------------------------ */
  /* Status bar clock                                                   */
  /* ------------------------------------------------------------------ */

  function tickClock() {
    $('lastUpdate').textContent = formatClock(new Date());
  }

  /* ------------------------------------------------------------------ */
  /* Sensor cards                                                       */
  /* FLASK HOOK: replace updateSensors() body with a fetch('/api/sensors')
     that returns { temperature, humidity, soilMoisture, light, wind, battery }
     and feed those numbers into the same DOM update calls below.        */
  /* ------------------------------------------------------------------ */

  const sensorIdMap = {
    temperature:  { value: 'tempValue',     status: 'tempStatus',     trend: 'tempTrend'     },
    humidity:     { value: 'humidityValue', status: 'humidityStatus', trend: 'humidityTrend' },
    soilMoisture: { value: 'moistureValue', status: 'moistureStatus', trend: 'moistureTrend' },
    light:        { value: 'lightValue',    status: 'lightStatus',    trend: 'lightTrend'    },
    wind:         { value: 'windValue',     status: 'windStatus',     trend: 'windTrend'     },
    battery:      { value: 'batteryValue',  status: 'batteryStatus',  trend: 'batteryTrend'  }
  };

  function statusForSensor(key, value) {
    switch (key) {
      case 'temperature':
        if (value >= 38) return { text: 'High', cls: 'status-good' };
        if (value <= 20) return { text: 'Low', cls: 'status-good' };
        return { text: 'Normal', cls: 'status-normal' };
      case 'humidity':
        if (value >= 80) return { text: 'High', cls: 'status-good' };
        return { text: 'Optimal', cls: 'status-optimal' };
      case 'soilMoisture':
        if (value <= 25) return { text: 'Low', cls: 'status-good' };
        return { text: 'Good', cls: 'status-good' };
      case 'light':
        return { text: 'Normal', cls: 'status-normal' };
      case 'wind':
        if (value >= 20) return { text: 'Gusty', cls: 'status-good' };
        return { text: 'Calm', cls: 'status-normal' };
      case 'battery':
        if (value <= 20) return { text: 'Low', cls: 'status-good' };
        return { text: 'Solar Charging', cls: 'status-optimal' };
      default:
        return { text: 'Normal', cls: 'status-normal' };
    }
  }

  function updateSensors() {
    const readings = {};

    Object.entries(state.sensors).forEach(([key, sensor]) => {
      const oldVal = sensor.value;
      const step = key === 'battery' ? 0.6 : (sensor.max - sensor.min) * 0.05;
      const newVal = key === 'battery'
        ? Math.round(clamp(oldVal + (Math.random() > 0.5 ? 0.2 : -0.1), 0, 100))
        : drift(oldVal, sensor.min, sensor.max, step);

      sensor.value = newVal;
      readings[key] = newVal;

      const ids = sensorIdMap[key];
      const valueEl = $(ids.value);
      if (valueEl) valueEl.textContent = newVal;

      const st = statusForSensor(key, newVal);
      const statusEl = $(ids.status);
      if (statusEl) {
        statusEl.textContent = st.text;
        statusEl.className = 'sensor-status ' + st.cls;
      }

      setTrend($(ids.trend), oldVal, newVal);
    });

    return readings;
  }

  /* ------------------------------------------------------------------ */
  /* Crop health ring                                                    */
  /* FLASK HOOK: swap the formula below for whatever score the backend /
     ML model returns, then reuse setHealthScore() to render it.         */
  /* ------------------------------------------------------------------ */

  const RING_CIRCUMFERENCE = 2 * Math.PI * 52; // r=52 from the SVG circle

  function computeHealthScore(readings) {
    const tempPenalty = Math.abs(readings.temperature - 27) * 1.1;
    const moisturePenalty = Math.max(0, 45 - readings.soilMoisture) * 0.8;
    const humidityPenalty = Math.max(0, readings.humidity - 75) * 0.6;
    const raw = 100 - tempPenalty - moisturePenalty - humidityPenalty;
    return clamp(Math.round(raw), 0, 100);
  }

  function setHealthScore(score) {
    const offset = RING_CIRCUMFERENCE - (score / 100) * RING_CIRCUMFERENCE;
    const ring = $('healthRingProgress');
    ring.style.strokeDasharray = String(RING_CIRCUMFERENCE);
    ring.style.strokeDashoffset = String(offset);

    let color = 'var(--accent)';
    let label = 'Healthy Crop';
    if (score < 50) { color = 'var(--critical)'; label = 'Crop At Risk'; }
    else if (score < 75) { color = 'var(--warning)'; label = 'Needs Attention'; }

    ring.style.stroke = color;
    $('healthScore').textContent = score + '%';
    $('healthStatusText').textContent = label;
    $('healthStatusText').style.color = color;
  }

  /* ------------------------------------------------------------------ */
  /* AI recommendation panel                                             */
  /* FLASK HOOK: this logic mirrors what a simple rules engine (or a
     model endpoint) on the Flask side would return as JSON, e.g.
     { temperature: "Normal", humidity: "Slightly High",
       moisture: "Low", action: "Start Irrigation", water: "8 Litres" } */
  /* ------------------------------------------------------------------ */

  function tagClass(level) {
    if (level === 'alert') return 'ai-tag tag-alert';
    if (level === 'warn') return 'ai-tag tag-warn';
    return 'ai-tag tag-normal';
  }

  function updateRecommendation(readings) {
    const tempLevel = readings.temperature >= 36 ? 'warn' : 'normal';
    const humidityLevel = readings.humidity >= 75 ? 'warn' : 'normal';
    const moistureLevel = readings.soilMoisture <= 30 ? 'alert' : 'normal';

    $('recTemp').textContent = tempLevel === 'warn' ? 'Rising' : 'Normal';
    $('recTemp').className = tagClass(tempLevel);

    $('recHumidity').textContent = humidityLevel === 'warn' ? 'Slightly High' : 'Normal';
    $('recHumidity').className = tagClass(humidityLevel);

    $('recMoisture').textContent = moistureLevel === 'alert' ? 'Low' : 'Sufficient';
    $('recMoisture').className = tagClass(moistureLevel);

    if (moistureLevel === 'alert') {
      const litres = Math.max(4, Math.round((30 - readings.soilMoisture) * 0.4));
      $('recAction').textContent = 'Start Irrigation';
      $('recWater').textContent = litres + ' Litres';
    } else {
      $('recAction').textContent = 'No Action Needed';
      $('recWater').textContent = '0 Litres';
    }
  }

  /* ------------------------------------------------------------------ */
  /* Alerts panel                                                        */
  /* ------------------------------------------------------------------ */

  function updateAlerts(readings) {
    const grid = $('alertsGrid');
    const alerts = [];

    if (readings.temperature >= 38) alerts.push({ icon: '⚠', text: 'Heat Stress' });
    if (readings.soilMoisture <= 25) alerts.push({ icon: '⚠', text: 'Low Moisture' });
    if (readings.humidity >= 82) alerts.push({ icon: '⚠', text: 'High Humidity' });
    if (readings.battery <= 20) alerts.push({ icon: '🔋', text: 'Battery Low' });
    if (readings.wind >= 22) alerts.push({ icon: '🌬', text: 'High Wind' });

    if (alerts.length === 0) {
      grid.innerHTML = '<div class="alert-card" style="background:var(--accent-soft);color:#2E6B39;border-color:transparent;">' +
        '<span class="alert-icon">✅</span><span class="alert-text">All Conditions Normal</span></div>';
      return;
    }

    grid.innerHTML = alerts.map(a =>
      `<div class="alert-card"><span class="alert-icon">${a.icon}</span><span class="alert-text">${a.text}</span></div>`
    ).join('');
  }

  /* ------------------------------------------------------------------ */
  /* Prediction section                                                  */
  /* FLASK HOOK: replace the +/- nudge with the model's forecast values. */
  /* ------------------------------------------------------------------ */

  function updatePrediction(readings) {
    const expectedTemp = Math.round((readings.temperature + 2) * 10) / 10;
    const expectedMoisture = Math.round((readings.soilMoisture - 2) * 10) / 10;

    $('predTempCurrent').textContent = readings.temperature + '°C';
    $('predTempExpected').textContent = expectedTemp + '°C';
    $('predMoistureCurrent').textContent = readings.soilMoisture + '%';
    $('predMoistureExpected').textContent = expectedMoisture + '%';
  }

  /* ------------------------------------------------------------------ */
  /* Live charts (Chart.js)                                              */
  /* FLASK HOOK: push the same readings pulled from /api/sensors into
     pushPoint() below instead of the simulated values.                 */
  /* ------------------------------------------------------------------ */

  function makeChart(canvasId, label, color) {
    const ctx = $(canvasId).getContext('2d');
    return new Chart(ctx, {
      type: 'line',
      data: {
        labels: [],
        datasets: [{
          label,
          data: [],
          borderColor: color,
          backgroundColor: color + '22',
          borderWidth: 2,
          pointRadius: 0,
          tension: 0.35,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: { legend: { display: false } },
        scales: {
          x: { display: false },
          y: { grid: { color: '#DCE5D2' }, ticks: { font: { family: 'JetBrains Mono', size: 10 } } }
        }
      }
    });
  }

  function pushPoint(chart, value) {
    const now = new Date();
    chart.data.labels.push(formatClock(now));
    chart.data.datasets[0].data.push(value);

    if (chart.data.labels.length > state.chartWindow) {
      chart.data.labels.shift();
      chart.data.datasets[0].data.shift();
    }
    chart.update();
  }

  function initCharts() {
    charts.temperature = makeChart('tempChart', 'Temperature', '#1F4D2C');
    charts.humidity = makeChart('humidityChart', 'Humidity', '#4C9A5A');
    charts.soilMoisture = makeChart('moistureChart', 'Soil Moisture', '#C97A24');
  }

  function updateCharts(readings) {
    pushPoint(charts.temperature, readings.temperature);
    pushPoint(charts.humidity, readings.humidity);
    pushPoint(charts.soilMoisture, readings.soilMoisture);
  }

  /* ------------------------------------------------------------------ */
  /* Main refresh loop                                                   */
  /* ------------------------------------------------------------------ */

  function refreshCycle() {
    const readings = updateSensors();
    const score = computeHealthScore(readings);
    setHealthScore(score);
    updateRecommendation(readings);
    updateAlerts(readings);
    updatePrediction(readings);
    updateCharts(readings);
    tickClock();
  }

  function startLoop() {
    if (state.timerId) clearInterval(state.timerId);
    state.timerId = setInterval(refreshCycle, state.refreshMs);
  }

  /* ------------------------------------------------------------------ */
  /* Power saving toggle                                                 */
  /* ------------------------------------------------------------------ */

  function initPowerToggle() {
    const toggle = $('powerToggle');
    toggle.addEventListener('click', () => {
      state.powerSaving = !state.powerSaving;
      state.refreshMs = state.powerSaving ? 5000 : 1000;

      toggle.setAttribute('aria-checked', String(state.powerSaving));
      $('refreshRateText').textContent = state.powerSaving ? '5 seconds' : '1 second';
      $('labelNormal').style.color = state.powerSaving ? 'var(--ink-muted)' : 'var(--primary)';
      $('labelSaving').style.color = state.powerSaving ? 'var(--primary)' : 'var(--ink-muted)';
      $('powerStatus').textContent = state.powerSaving ? 'Power Saving' : 'Normal';

      startLoop();
    });
  }

  /* ------------------------------------------------------------------ */
  /* Disease detection upload                                            */
  /* FLASK HOOK: on Analyze, POST the file to /api/detect-disease and
     render the returned label/confidence instead of the random pick.   */
  /* ------------------------------------------------------------------ */

  function initDiseaseUpload() {
    const input = $('leafInput');
    const dropzone = $('uploadDropzone');
    const preview = $('leafPreview');
    const icon = $('uploadIcon');
    const chooseBtn = $('chooseFileBtn');
    const analyzeBtn = $('analyzeBtn');
    const resultText = $('diseaseResultText');

    chooseBtn.addEventListener('click', () => input.click());
    dropzone.addEventListener('click', () => input.click());

    ['dragover', 'dragenter'].forEach(evt =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.style.borderColor = 'var(--accent)';
      })
    );
    ['dragleave', 'drop'].forEach(evt =>
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.style.borderColor = '';
      })
    );
    dropzone.addEventListener('drop', (e) => {
      const file = e.dataTransfer.files[0];
      if (file) {
        input.files = e.dataTransfer.files;
        showPreview(file);
      }
    });

    input.addEventListener('change', () => {
      const file = input.files[0];
      if (file) showPreview(file);
    });

    function showPreview(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        preview.src = e.target.result;
        preview.hidden = false;
        icon.hidden = true;
      };
      reader.readAsDataURL(file);
      resultText.textContent = 'Awaiting Analysis';
      resultText.className = 'result-value';
    }

    analyzeBtn.addEventListener('click', () => {
      if (!input.files[0]) {
        resultText.textContent = 'Upload An Image First';
        resultText.className = 'result-value result-warning';
        return;
      }

      resultText.textContent = 'Analyzing…';
      resultText.className = 'result-value';

      // Dummy classification — replace with the /api/detect-disease response.
      setTimeout(() => {
        const outcomes = [
          { text: 'Healthy Leaf', cls: 'result-healthy' },
          { text: 'Early Blight Detected', cls: 'result-warning' },
          { text: 'Leaf Spot Detected', cls: 'result-critical' }
        ];
        const pick = outcomes[Math.floor(Math.random() * outcomes.length)];
        resultText.textContent = pick.text;
        resultText.className = 'result-value ' + pick.cls;
      }, 900);
    });
  }

  /* ------------------------------------------------------------------ */
  /* Mobile nav toggle                                                    */
  /* ------------------------------------------------------------------ */

  function initNavToggle() {
    const btn = $('navToggle');
    const nav = document.querySelector('.main-nav');
    const badges = document.querySelector('.header-badges');

    btn.addEventListener('click', () => {
      const isOpen = btn.getAttribute('aria-expanded') === 'true';
      btn.setAttribute('aria-expanded', String(!isOpen));

      [nav, badges].forEach(el => {
        if (!el) return;
        el.style.display = isOpen ? '' : 'flex';
        el.style.position = isOpen ? '' : 'absolute';
        el.style.top = isOpen ? '' : '64px';
        el.style.left = isOpen ? '' : '0';
        el.style.right = isOpen ? '' : '0';
        el.style.flexDirection = isOpen ? '' : 'column';
        el.style.background = isOpen ? '' : 'var(--surface)';
        el.style.padding = isOpen ? '' : '14px 20px';
        el.style.borderBottom = isOpen ? '' : '1px solid var(--surface-line)';
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Init                                                                 */
  /* ------------------------------------------------------------------ */

  document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initPowerToggle();
    initDiseaseUpload();
    initNavToggle();
    refreshCycle();   // paint immediately instead of waiting for first interval
    startLoop();
  });

})();