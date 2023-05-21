from flask import Flask, jsonify, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import paho.mqtt.client as mqtt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

login_manager = LoginManager(app)

class User(UserMixin):
    def __init__(self, id, password_hash):
        self.id = id
        self.password_hash = password_hash

# Miejsce przechowywania naszych "użytkowników" i ich haseł
users = {}

# MQTT broker configuration
mqtt_broker = 'localhost'
mqtt_port = 1883
mqtt_topic = 'puls'

# MQTT client setup
mqtt_client = mqtt.Client()

@login_manager.user_loader
def load_user(user_id):
    if user_id in users:
        return User(user_id, users[user_id])
    return None

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users:
            return "User already exists", 400
        else:
            users[username] = generate_password_hash(password)
            user = User(username, users[username])
            login_user(user)
            return redirect(url_for('index'))
    else:
        return '''
            <form method="POST">
                Username: <input type="text" name="username"><br>
                Password: <input type="password" name="password"><br>
                <input type="submit" value="Submit">
            </form>
        '''

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users and check_password_hash(users[username], password):
            user = User(username, users[username])
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "Invalid credentials", 401
    else:
        return '''
            <form method="POST">
                Username: <input type="text" name="username"><br>
                Password: <input type="password" name="password"><br>
                <input type="submit" value="Submit">
            </form>
        '''

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Endpoint do pobierania danych pulsów
@app.route('/puls', methods=['GET'])
@login_required
def get_puls():
    # Tutaj dodaj kod do odczytu danych pulsów
    return jsonify({'puls': None})

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(mqtt_topic)
    else:
        print("Failed to connect to MQTT broker")

def on_message(client, userdata, msg):
    payload = msg.payload.decode('utf-8')
    # Przetwarzanie odebranych danych z MQTT
    print("Received puls data:", payload)

# Setup MQTT client callbacks
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Start MQTT client in a separate thread
mqtt_client.loop_start()

# Endpoint str
@app.route('/')
@login_required
def index():
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
        </body>
        </html>
    '''

if __name__ == '__main__':
    # Connect to MQTT broker
    mqtt_client.connect(mqtt_broker, mqtt_port, 60)

    app.run(host='0.0.0.0', port=5000, debug=True) 


