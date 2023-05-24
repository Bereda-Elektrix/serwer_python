from flask import Flask, jsonify, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
import paho.mqtt.client as mqtt
import random
import threading
import hashlib

app = Flask(__name__)
app.secret_key = "secret_key"  # Sekretne klucz sesji

# Konfiguracja Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Zmienna globalna do przechowywania pulsów
cached_pulse = None
lock = threading.Lock()

# Konfiguracja MQTT
mqtt_server = "localhost"
mqtt_port = 1883
mqtt_topic = "test/puls"

# Proste przechowywanie danych logowania
users = {"admin": {"password": "admin", "hashed_password": hashlib.sha256("admin".encode()).hexdigest()}}

# Klasa użytkownika zgodna z interfejsem UserMixin
class User(UserMixin):
    pass

# Funkcja do ładowania użytkownika na podstawie nazwy użytkownika
@login_manager.user_loader
def load_user(username):
    if username in users:
        user = User()
        user.id = username
        return user

# Obsługa połączenia z brokerem MQTT
def on_connect(client, userdata, flags, rc):
    print("Połączono z brokerem MQTT")
    client.subscribe(mqtt_topic)

# Obsługa otrzymanych wiadomości MQTT
def on_message(client, userdata, msg):
    global cached_pulse
    puls = msg.payload.decode()
    with lock:
        cached_pulse = puls

# Inicjalizacja klienta MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_server, mqtt_port, 60)
client.loop_start()

# Strona rejestracji - teraz domyślna strona
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Sprawdzenie, czy użytkownik już istnieje
        if username in users:
            return "User already exists"
        if len(password) < 8 or any(ele.isupper() for ele in password)==0 or password.isalpha():
            return "Password must contain 8 or more letters, have one big letter and one special letter"
        # Haszowanie hasła
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Dodanie użytkownika do słownika
        users[username] = {"password": password, "hashed_password": hashed_password}

        return redirect(url_for('login'))

    # Prosta forma rejestracji 
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Register">
        </form>
        <br>
        <a href="/login">Login</a>
    '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Sprawdzenie, czy użytkownik istnieje i czy hasło jest poprawne
        if username in users and hashlib.sha256(password.encode()).hexdigest() == users[username]["hashed_password"]:
            user =User()
            user.id = username
            login_user(user)  # Logowanie użytkownika
            return redirect(url_for('data'))

        return "Invalid credentials"

    # Prosta forma logowania 
    return '''
        <form method="post">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
        <br>
        <a href="/">Register</a>
    '''

# Endpoint do wylogowania użytkownika
@app.route('/logout')
@login_required
def logout():
    logout_user()  # Wylogowanie użytkownika
    return redirect(url_for('index'))

# Endpoint do pobierania danych pulsów
@app.route('/puls', methods=['GET'])
@login_required
def get_puls():
    with lock:
        puls = cached_pulse
    return jsonify({'puls': puls})

# Endpoint dla strony z danymi
@app.route('/data')
@login_required
def data():
    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Real Time Puls Data</title>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
            <script>
                function getPulsData() {
                    $.ajax({
                        url: '/puls',
                        type: 'GET',
                        success: function(response) {
                            $('#pulsData').text('Received Puls: ' + response.puls);
                        },
                        error: function() {
                            $('#pulsData').text('Failed to fetch puls data');
                        },
                        complete: function() {
                            setTimeout(getPulsData, 1000);
                        }
                    });
                }
                
                $(document).ready(function() {
                    getPulsData();
                });
            </script>
        </head>
        <body>
            <div id="pulsData">Waiting for Puls data...</div>
            <br>
            <a href="/logout">Logout</a>
        </body>
        </html>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=('c:/Users/2020/Desktop/Bemsi projekt/certyfikaty/server.crt', 'c:/Users/2020/Desktop/Bemsi projekt/certyfikaty/ca.key'))
