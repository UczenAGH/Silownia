from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)
IOT_URL = "http://localhost:5000"

workout_log = []
current_exercise = "Bench Press"
THRESHOLD = 80 

def calculate_reps(data):
    if len(data) < 5: return 0, 0 
    reps = 0
    max_z = 0
    for i in range(1, len(data) - 1):
        z_prev = data[i-1]["accelerometer"][2]
        z_curr = data[i]["accelerometer"][2]
        z_next = data[i+1]["accelerometer"][2]
        if z_curr > max_z: max_z = z_curr
        if z_curr > THRESHOLD and z_curr >= z_prev and z_curr >= z_next:
            reps += 1
    return reps, round(max_z, 2)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, threshold=THRESHOLD)

@app.route('/app/start', methods=['POST'])
def app_start():
    try:
        requests.post(f"{IOT_URL}/iot/start", timeout=1)
        return jsonify({"status": "started"})
    except: return jsonify({"error": "Błąd IoT"}), 503

@app.route('/app/stop', methods=['POST'])
def app_stop():
    try:
        response = requests.post(f"{IOT_URL}/iot/stop", timeout=2)
        iot_payload = response.json()
        raw_data = iot_payload.get("workout_data", [])
        total_reps, peak = calculate_reps(raw_data)
        workout_log.append({"exercise": current_exercise, "reps": total_reps, "peak": peak})
        return jsonify({
            "total_reps": total_reps, 
            "max_peak": peak, 
            "raw_data": raw_data, 
            "threshold": THRESHOLD,
            "exercise": current_exercise
        })
    except: return jsonify({"error": "Błąd danych"}), 503

@app.route('/app/log', methods=['GET'])
def get_log():
    return jsonify(workout_log)

@app.route('/app/set_exercise', methods=['POST'])
def set_exercise():
    global current_exercise
    data = request.get_json()
    current_exercise = data.get("exercise", "Bench Press")
    return jsonify({"status": "ok", "exercise": current_exercise})

# --- SZABLON HTML (DODANO PANEL REJESTRACJI) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <title>SmartGYM Pro</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {
            --background: #000000;
            --card: #1C1C1E;
            --primary: #00C0DB;
            --text: #FFFFFF;
            --text-muted: #8E8E93;
            --input-bg: #B0BEC5;
            --accent-yellow: #F1C40F;
            --error: #FF453A;
        }

        body { font-family: -apple-system, sans-serif; background: var(--background); color: var(--text); display: flex; flex-direction: column; align-items: center; padding: 20px; }
        .panel { background: var(--card); border-radius: 14px; padding: 24px; width: 100%; max-width: 400px; text-align: center; margin-bottom: 20px; border: 1px solid #333; }
        .hidden { display: none; }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: none; background: var(--input-bg); color: #000; font-weight: bold; box-sizing: border-box; }
        button { width: 100%; padding: 14px; margin-top: 10px; border-radius: 10px; border: none; font-weight: bold; cursor: pointer; text-transform: uppercase; }
        .btn-p { background: var(--primary); color: #000; }
        .btn-o { background: transparent; border: 1px solid var(--primary); color: var(--primary); }
        .stat-box { background: #2C2C2E; padding: 15px; border-radius: 10px; flex: 1; border: 1px solid #333; }
        .neon-val { color: var(--primary); font-size: 32px; font-weight: bold; }
        .gold-val { color: var(--accent-yellow); font-size: 32px; font-weight: bold; }
        select { width: 100%; padding: 12px; border-radius: 8px; background: var(--card); color: white; border: 1px solid #333; margin-bottom: 15px; }
        table { width: 100%; font-size: 12px; border-collapse: collapse; margin-top: 10px; }
        tr { border-bottom: 1px solid #333; } td { padding: 8px; }
    </style>
</head>
<body>

    <div id="authPanel" class="panel">
        <h1 style="color: var(--primary)">SmartGYM Pro</h1>
        
        <div id="loginForm">
            <h2>Logowanie</h2>
            <input type="text" id="username" placeholder="Login">
            <input type="password" id="password" placeholder="Hasło">
            <button class="btn-p" onclick="handleAuth()">Zaloguj</button>
            <button class="btn-o" onclick="toggleAuth(false)">Nie masz konta? Zarejestruj się</button>
        </div>

        <div id="registerForm" class="hidden">
            <h2>Rejestracja</h2>
            <input type="text" id="regUsername" placeholder="Nowy Login">
            <input type="password" id="regPassword" placeholder="Hasło">
            <input type="password" id="regPasswordConfirm" placeholder="Powtórz Hasło">
            <button class="btn-p" onclick="handleRegister()">Załóż konto</button>
            <button class="btn-o" onclick="toggleAuth(true)">Powrót do logowania</button>
        </div>
    </div>

    <div id="appPanel" class="panel hidden" style="max-width: 600px;">
        <div style="display:flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <p style="font-size: 12px; margin:0;">Zalogowano: <b id="userLabel" style="color:var(--primary)"></b></p>
            <button class="btn-o" style="width: auto; padding: 5px 10px; margin:0; font-size: 10px;" onclick="logout()">Wyloguj</button>
        </div>

        <select id="exerciseSelect" onchange="updateExercise()">
            <option>Bench Press</option><option>Squat</option><option>Deadlift</option>
            <option>Overhead Press</option><option>Lat Pulldown</option>
        </select>

        <div style="display: flex; gap: 10px;">
            <button class="btn-p" id="startBtn" onclick="startWorkout()">START</button>
            <button class="btn-o" id="stopBtn" onclick="stopWorkout()" disabled style="color:var(--error); border-color:var(--error);">STOP</button>
        </div>

        <div id="results" class="hidden">
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <div class="stat-box">REPS<br><span id="repsVal" class="neon-val">0</span></div>
                <div class="stat-box">PEAK<br><span id="peakVal" class="gold-val">0</span></div>
            </div>
            <canvas id="workoutChart" style="margin: 20px 0;"></canvas>
            <button class="btn-p" style="background: var(--accent-yellow); color:black;" onclick="syncWorkout()">☁ synchronizacja z serwerem</button>
        </div>

        <div style="margin-top: 30px; text-align: left;">
            <h3 style="color: var(--primary)">historia treningów</h3>
            <div id="historyTable"></div>
        </div>
    </div>

    <script>
        const AUTH_SRV = "http://localhost:10000";
        let myChart = null;

        // Przełączanie widoków logowanie/rejestracja
        function toggleAuth(showLogin) {
            document.getElementById('loginForm').className = showLogin ? '' : 'hidden';
            document.getElementById('registerForm').className = showLogin ? 'hidden' : '';
        }

        // Obsługa logowania
        async function handleAuth() {
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            const res = await fetch(`${AUTH_SRV}/login`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: u, password: p})
            });
            const data = await res.json();
            if(res.ok) {
                localStorage.setItem('token', data.token);
                localStorage.setItem('user', data.username);
                showApp();
            } else alert(data.error);
        }

        // --- NOWY ENDPOINT REJESTRACJI Z WALIDACJĄ HASŁA ---
        async function handleRegister() {
            const u = document.getElementById('regUsername').value;
            const p = document.getElementById('regPassword').value;
            const p2 = document.getElementById('regPasswordConfirm').value;

            if (p !== p2) {
                alert("Błąd: Hasła nie są identyczne!");
                return;
            }

            const res = await fetch(`${AUTH_SRV}/register`, {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username: u, password: p})
            });
            const data = await res.json();
            if(res.ok) {
                alert("Konto utworzone pomyślnie");
                toggleAuth(true);
            } else alert(data.error);
        }

        function showApp() {
            document.getElementById('authPanel').classList.add('hidden');
            document.getElementById('appPanel').classList.remove('hidden');
            document.getElementById('userLabel').innerText = localStorage.getItem('user');
            loadHistory();
        }

        function logout() { localStorage.clear(); location.reload(); }

        async function updateExercise() {
            const ex = document.getElementById('exerciseSelect').value;
            await fetch('/app/set_exercise', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({exercise: ex})
            });
        }

        async function startWorkout() {
            await fetch('/app/start', {method: 'POST'});
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
        }

        async function stopWorkout() {
            const res = await fetch('/app/stop', {method: 'POST'});
            const data = await res.json();
            document.getElementById('repsVal').innerText = data.total_reps;
            document.getElementById('peakVal').innerText = data.max_peak;
            document.getElementById('results').classList.remove('hidden');
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            drawChart(data.raw_data, data.threshold);
        }

        async function syncWorkout() {
            const payload = {
                exercise: document.getElementById('exerciseSelect').value,
                reps: document.getElementById('repsVal').innerText,
                peak: document.getElementById('peakVal').innerText
            };
            const res = await fetch(`${AUTH_SRV}/sync`, {
                method: 'POST',
                headers: {
                    'Authorization': localStorage.getItem('token'),
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            if(res.ok) { alert("Zsynchronizowano!"); loadHistory(); }
        }

        async function loadHistory() {
            const res = await fetch(`${AUTH_SRV}/history`, {
                headers: {'Authorization': localStorage.getItem('token')}
            });
            const data = await res.json();
            let html = '<table><tr><td>DATA</td><td>ĆWICZENIE</td><td>REPS</td><td>PEAK</td></tr>';
            data.forEach(h => {
                html += `<tr>
                    <td>${h.date.slice(5, 16)}</td>
                    <td>${h.exercise}</td>
                    <td style="color:var(--primary)">${h.reps}</td>
                    <td style="color:var(--accent-yellow)">${h.peak}</td>
                </tr>`;
            });
            document.getElementById('historyTable').innerHTML = html + '</table>';
        }

        function drawChart(rawData, threshold) {
            const ctx = document.getElementById('workoutChart').getContext('2d');
            const z = rawData.map(p => p.accelerometer[2]);
            if(myChart) myChart.destroy();
            myChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: z.map((_, i) => i),
                    datasets: [{
                        label: 'Ruch Z', data: z, borderColor: '#00C0DB', tension: 0.4, pointRadius: 0
                    }, {
                        label: 'Próg', data: new Array(z.length).fill(threshold), borderColor: 'red', borderDash: [5, 5], pointRadius: 0
                    }]
                },
                options: { scales: { x: { display: false }, y: { grid: { color: '#333' } } }, plugins: { legend: { display: false } } }
            });
        }

        window.onload = () => { if(localStorage.getItem('token')) showApp(); };
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(port=8080, debug=False)