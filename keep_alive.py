# Keeps the bot alive
from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def main():
    return "Your bot is alive!"


def run():
    app.run(host="0.0.0.0", port=8080)


# This function keeps the bot alive
def keep_alive():
    server = Thread(target=run)
    server.start()
