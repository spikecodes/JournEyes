from flask import Flask, send_file
import pyautogui
import tempfile
import os

app = Flask(__name__)

@app.route('/screenshot')
def takescreenshot():
    screenshot = pyautogui.screenshot()

    screenshot_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    screenshot.save(screenshot_file.name)

    response = send_file(screenshot_file.name, mimetype='image/png')

    return response

if __name__ == '__main__':
    app.run(debug=True, port=8000)