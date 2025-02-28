from flask import Flask, render_template, request, redirect, url_for
import time
import datetime
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for
app = Flask(__name__)
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
app.secret_key = env.get("APP_SECRET_KEY")
oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)
tags = {
    "Work": "#aae364",
    "Personal": "#4e76d4",
    "Urgent": "#cf0000",
}

filtered_tag = ""
default_datetime = datetime.datetime(1971,1,1,0,0)
default_description = "Enter description here: "
sort = 0

#  id: [task_name, completed, [tag_names], recently_added], datetime, description, description_rows}
tasks = {
    0: ["Task 1", 0, ["Work", "Urgent"], 0, default_datetime, "Task 1 now has a description", 1],
    1: ["Task 2", 0, ["Personal"], 0, default_datetime, default_description, 1],
    2: ["Task 3", 0, ["Urgent"], 0, default_datetime, default_description, 1]
}

current_index = len(tasks)


def colour_intensity(hex):
  hex = hex.replace("#","")
  return sum(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4)))/3
app.jinja_env.globals.update(colour_intensity = colour_intensity)

def reset_recently_added(task):
  tasks[task][3] = 0
app.jinja_env.globals.update(reset_recently_added = reset_recently_added)
#log in routes
@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("index", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

#other routes
@app.route('/')
def index():
    global sort
    if sort:
        if filtered_tag == "":
            checked_tasks = {k: v for k, v in reversed({k: v for k, v in sorted(tasks.items(), key = lambda item: item[1][4].timestamp()) if v[1] == 1}.items())}
            unchecked_tasks = {k: v for k, v in reversed({k: v for k, v in sorted(tasks.items(), key = lambda item: item[1][4].timestamp()) if v[1] == 0}.items())}
        else:
            checked_tasks = {k: v for k, v in reversed({k: v for k, v in sorted(tasks.items(), key = lambda item: item[1][4].timestamp()) if v[1] == 1 and filtered_tag in v[2]}.items())}
            unchecked_tasks = {k: v for k, v in reversed({k: v for k, v in sorted(tasks.items(), key = lambda item: item[1][4].timestamp()) if v[1] == 0 and filtered_tag in v[2]}.items())}
    else:
        if filtered_tag == "":
            checked_tasks = {k: v for k, v in reversed({k: v for k, v in tasks.items() if v[1] == 1}.items())}
            unchecked_tasks = {k: v for k, v in reversed({k: v for k, v in tasks.items() if v[1] == 0}.items())}
        else:
            checked_tasks = {k: v for k, v in reversed({k: v for k, v in tasks.items() if v[1] == 1 and filtered_tag in v[2]}.items())}
            unchecked_tasks = {k: v for k, v in reversed({k: v for k, v in tasks.items() if v[1] == 0 and filtered_tag in v[2]}.items())}
    tasks_arg = unchecked_tasks.copy()
    tasks_arg.update(checked_tasks)
    return render_template('index.html', tasks=tasks_arg,tags=tags,filtered_tag=filtered_tag,sort_datetime=sort,session=session.get('user'), pretty=json.dumps(session.get('user'), indent=4))

@app.route('/add', methods=['POST'])
def add_task():
    global current_index
    new_task = request.form.get('newTask') 
    if new_task:
        tasks[current_index] = [new_task, 0, [], 1, default_datetime, default_description, 1]
        current_index += 1
    return redirect(url_for('index'))

@app.route('/complete', methods=['POST'])
def complete_tasks():
    completed_tasks = request.form.getlist('checkboxId')
    for index in map(int, completed_tasks):
         if 0 <= index < current_index:
            if int(request.form["currentlyChecked"]):
                tasks[index][1] = 0
            else:
                tasks[index][1] = 1
            tasks[index][3] = 1

    time.sleep(0.5)

    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_tasks():
    task_index = request.form.get('taskIndex')
    
    if task_index is not None:
        index = int(task_index)
        if 0 <= index < current_index:
            tasks.pop(index,None)

    time.sleep(0.5)

    return redirect(url_for('index'))

@app.route('/add_tag', methods=['POST'])
def add_tag():
    tag = request.form.get('tagSelected')
    task_index = int(request.form.get('taskIndex'))
    tasks[task_index][2] += [tag]

    return redirect(url_for('index'))

@app.route('/delete_tag', methods=['POST'])
def delete_tag():
    tag = request.form.get('tagSelected')
    task_index = int(request.form.get('taskIndex'))
    tasks[task_index][2].remove(tag)

    return redirect(url_for('index'))

@app.route('/create_tag', methods=['POST'])
def create_tag():
    tag = request.form.get('tagCreated')

    colour = request.form.get('newTagColour')
    tags[tag] = colour

    print(tag, colour)

    return redirect(url_for('index'))

@app.route('/filter_tasks', methods=['POST'])
def filter_tasks():
    global filtered_tag
    filtered_tag = request.form.get('tagsFilterList')

    return redirect(url_for('index'))

@app.route('/update_time', methods=['POST'])
def update_time():
    time = request.form.get('timeSelector')
    index = int(request.form.get('taskIndex'))
    time = time.split('T')
    time[0] = time[0].split('-')
    time[1] = time[1].split(':')
    time[0] += time[1]
    time = datetime.datetime(*map(int, time[0]))
    tasks[index][4] = time
    return redirect(url_for('index'))

@app.route('/sort_by_datetime', methods=['POST'])
def sort_by_datetime():
    global sort
    checked = request.form.get('datetimeSortCheckbox')
    if checked == "on":
        sort = 1
    else:
        sort = 0

    return redirect(url_for('index'))

@app.route('/edit_description', methods=['POST'])
def edit_description():
    text = request.form.get('descriptionText')
    index = int(request.form.get('taskIndex'))
    rows = int(request.form.get('descriptionRows'))

    tasks[index][5] = text
    if text == "":
        tasks[index][5] = default_description
        
    tasks[index][6] = rows

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0", port=env.get("PORT", 3000))
