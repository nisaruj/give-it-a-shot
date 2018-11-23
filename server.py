from flask import Flask, render_template, redirect
from flask_socketio import SocketIO
import pyautogui
import math

app = Flask(__name__)
app.config['SECRET_KEY'] = 'compengess'
socketio = SocketIO(app)

"""Gyro class 
contains three angles and distance from shooter to screen (cm)
"""
class Gyro:
    def __init__(self, alpha, beta, gamma, dist):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.dist = dist

    def diffAlpha(self, other):
        return ((((self.alpha - other.alpha) % 360) + 540) % 360) - 180

    def __str__(self):
        return 'Gyro(' + str(self.alpha) + ',' + str(self.beta) + ',' + str(self.gamma) + ')'

    def __repr__(self):
        return 'Gyro(' + str(self.alpha) + ',' + str(self.beta) + ',' + str(self.gamma) + ')'

"""Point class
contains point(x, y) in percentage
"""
class Point:
    def __init__(self, x, y):
        self.x = int(x * 100)
        self.y = int(y * 100)

    def __str__(self):
        return '[' + str(self.x) + ',' + str(self.y) + ']'

    def __repr__(self):
        return 'Point(' + str(self.x) + ',' + str(self.y) + ')'

""" Global variables """
gyros = []
finishCalibrate = False
shots = []
screenSize = {}

""" Trigonometry functions """
def calculateHLen(normalLength, center, gyro):
    dAlpha = center.diffAlpha(gyro)
    return normalLength * math.tan(math.radians(dAlpha))

def calculateVLen(normalLength, center, gyro):
    dAlpha = center.diffAlpha(gyro)
    return normalLength * math.tan(math.radians(gyro.beta)) / math.cos(math.radians(dAlpha))

def calculateSize(gyros):
    normalLength = gyros[0].dist * math.cos(math.radians(gyros[0].beta))
    w1 = abs((calculateHLen(normalLength, gyros[0], gyros[1]) + calculateHLen(normalLength, gyros[0], gyros[4])) / 2)
    w2 = abs((calculateHLen(normalLength, gyros[0], gyros[2]) + calculateHLen(normalLength, gyros[0], gyros[3])) / 2)
    h1 = abs((calculateVLen(normalLength, gyros[0], gyros[1]) + calculateVLen(normalLength, gyros[0], gyros[2])) / 2)
    h2 = abs((calculateVLen(normalLength, gyros[0], gyros[3]) + calculateVLen(normalLength, gyros[0], gyros[4])) / 2)
    return {'width': w1 + w2, 'height': h1 + h2}

""" Get screen resolution """
def getResolution():
    return pyautogui.size()

""" Index """
@app.route("/")
def index():
    return "It's working!<br><a href='/gun'>Open virtual gun</a><br><a href='/cursor'>Open virtual cursor</a>"

""" Reset calibrate setting """
@app.route("/reset")
def reset():
    global gyros
    global finishCalibrate
    gyros = []
    finishCalibrate = False
    return redirect("/cursor", code=302)

""" Virtual gun """
@app.route("/gun")
def gun():
    return render_template("gun.html")

""" Virtual target """
@app.route("/target")
def target():
    return render_template("target.html", shots = shots)

""" Cursor test """
@app.route("/cursor")
def cursor():
    return render_template("cursor.html")

""" Shoot """
@app.route("/shoot/<alpha>/<beta>/<gamma>/<dist>/<isClicked>")
def shoot(alpha, beta, gamma, dist, isClicked):
    global finishCalibrate
    global shots
    global gyros
    if not finishCalibrate:
        return "Please calibrate first"

    alpha = int(alpha)
    beta = int(beta)
    gamma = int(gamma)
    dist = int(dist)
    shotAngle = Gyro(alpha, beta, gamma, dist)
    halfWidth = screenSize['width'] / 2
    halfHeight = screenSize['height'] / 2
    normalLength = gyros[0].dist * math.cos(math.radians(gyros[0].beta))

    X = halfWidth + calculateHLen(normalLength, gyros[0], shotAngle)
    Y = halfHeight - calculateVLen(normalLength, gyros[0], shotAngle)

    ''' Deprecated, use socketIO instread
    shots.append(str(Point(X / screenSize['width'], Y / screenSize['height'])))
    print(shots)
    '''

    socketio.emit('shoot', {'x': X / screenSize['width'] * 100, 'y': Y / screenSize['height'] * 100})
    pyautogui.moveTo(X * getResolution()[0] / screenSize['width'], Y * getResolution()[1] / screenSize['height'])
    isClicked = int(isClicked)
    if isClicked:
        pyautogui.click()
    return "OK"

""" Calibrate """
@app.route("/calibrate/<alpha>/<beta>/<gamma>/<dist>")
def calibrate(alpha, beta, gamma, dist):
    global gyros
    global finishCalibrate

    if finishCalibrate:
        return "Already calibrated"

    alpha = int(alpha)
    beta = int(beta)
    gamma = int(gamma)
    dist = int(dist)

    if beta < -90 or beta > 90:
        socketio.emit('calibrate', {'error': True, 'step': len(gyros)} )
        return "Error"

    gyros.append(Gyro(alpha, beta, gamma, dist))
    print(gyros)
    socketio.emit('calibrate', {'error': False, 'step': len(gyros)} )

    if len(gyros) == 5:
        global screenSize
        finishCalibrate = True
        screenSize = calculateSize(gyros)
        print('\n***** The screen size is ' + str(screenSize['width']) + ' x ' + str(screenSize['height']) + '  *****\n')
        return "Finished"

    return "OK"

""" Main function """
if __name__ == "__main__":
    socketio.run(app, debug=True, host="0.0.0.0")
    #app.run(host="0.0.0.0")