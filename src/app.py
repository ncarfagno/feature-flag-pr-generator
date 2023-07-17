import os
import configparser
from github import Github
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)

def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    github_config = config['Github']

    username = github_config.get('username')
    token = github_config.get('token')
    repository = github_config.get('repository')
    title = github_config.get('title')
    body = github_config.get('body')
    head = github_config.get('head')
    base = github_config.get('base')

    return username, token, repository, title, body, head, base

def write_config(username, token, repository, title, body, head, base):
    config = configparser.ConfigParser()
    config['Github'] = {
        'username': username,
        'token': token,
        'repository': repository,
        'title': title,
        'body': body,
        'head': head,
        'base': base
    }

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def create_pull_request(username, token, repository, title, body, head, base):
    g = Github(username, token)
    repo = g.get_repo(repository)
    return repo.create_pull(title=title, body=body, head=head, base=base)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Handle the form submission to modify the configuration file
        username = request.form.get("username")
        token = request.form.get("token")
        repository = request.form.get("repository")
        title = request.form.get("title")
        body = request.form.get("body")
        head = request.form.get("head")
        base = request.form.get("base")

        write_config(username, token, repository, title, body, head, base)
        flash("Configuration updated successfully!", "success")

    # Read the current configuration file and display it in the front-end
    username, token, repository, title, body, head, base = read_config()

    return render_template("index.html", username=username, token=token, repository=repository,
                           title=title, body=body, head=head, base=base)

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)