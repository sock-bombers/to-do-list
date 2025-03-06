from flask import Flask, render_template, request, redirect, url_for, jsonify, session
from authlib.integrations.flask_client import OAuth
import time
import datetime
import json
from os import environ as env
from dotenv import find_dotenv, load_dotenv
from urllib.parse import quote_plus, urlencode
from auth0.authentication import GetToken
from auth0.management import Auth0

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)
    
app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

domain = env.get("AUTH0_DOMAIN")

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{domain}/.well-known/openid-configuration'
)

get_token = GetToken(domain, env.get("OAUTH_CLIENT_ID"), client_secret=env.get("OAUTH_CLIENT_SECRET"))
token = get_token.client_credentials('https://{}/api/v2/'.format(domain))
mgmt_api_token = token['access_token']
auth0 = Auth0(domain, mgmt_api_token)

tags = {
    "Work": "#aae364",
    "Personal": "#4e76d4",
    "Urgent": "#cf0000",
}

filtered_tag = ""
default_datetime = datetime.datetime(1971,1,1,0,0)
default_description = "Enter description here: "
sort = 0
logged_in = False

#  id: [task_name, completed, [tag_names], recently_added], datetime, description, description_rows}
tasks = {}
current_index = len(tasks)

def update_db():
    if session.get('user'):
        auth0.users.update(session.get('user')['userinfo']['sub'], {
            'user_metadata': {
                "tasks":json.dumps(tasks, default=str),
                "tags":json.dumps(tags, default=str)
            }
        })

def colour_intensity(hex):
  hex = hex.replace("#","")
  return sum(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4)))/3
app.jinja_env.globals.update(colour_intensity = colour_intensity)

def reset_recently_added(task):
  tasks[task][3] = 0
app.jinja_env.globals.update(reset_recently_added = reset_recently_added)


@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    global tasks
    global tags
    global logged_in
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    if session.get('user'):
        id = session.get('user')['userinfo']['sub']
        user = auth0.users.list(search_engine='v3', q='user_id='+id)['users'][0]
        data = user['user_metadata']
        tasks = json.loads(data["tasks"])
        tags = json.loads(data["tags"])
        tasks = {int(i):tasks[i][0:4]+[datetime.datetime.strptime(tasks[i][4],'%Y-%m-%d %H:%M:%S')]+tasks[i][5:] for i in tasks}
        logged_in = True

    return redirect("/")

@app.route("/logout")
def logout():
    global tasks
    global current_index
    global logged_in
    global tags
    session.clear()
    tasks = {}
    current_index = len(tasks)
    logged_in = False
    tags = {
    "Work": "#aae364",
    "Personal": "#4e76d4",
    "Urgent": "#cf0000",
    }
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


@app.route('/')
def index():
    global tasks
    global tags
    global logged_in
    if session.get('user') and not logged_in:
        id = session.get('user')['userinfo']['sub']
        user = auth0.users.list(search_engine='v3', q='user_id='+id)['users'][0]
        data = user['user_metadata']
        tasks = json.loads(data["tasks"])
        tags = json.loads(data["tags"])
        tasks = {int(i):tasks[i][0:4]+[datetime.datetime.strptime(tasks[i][4],'%Y-%m-%d %H:%M:%S')]+tasks[i][5:] for i in tasks}
        logged_in = True

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

    return render_template('index.html', tasks=tasks_arg,tags=tags,filtered_tag=filtered_tag,sort_datetime=sort, session=session.get('user'))

@app.route('/add', methods=['POST'])
def add_task():
    global current_index
    new_task = request.form.get('newTask') 
    if new_task:
        tasks[current_index] = [new_task, 0, [], 1, default_datetime, default_description, 1]
        current_index += 1

    update_db()

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

    update_db()

    time.sleep(0.5)

    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_tasks():
    task_index = request.form.get('taskIndex')
    
    if task_index is not None:
        index = int(task_index)
        if 0 <= index < current_index:
            tasks.pop(index,None)

    update_db()

    time.sleep(0.5)

    return redirect(url_for('index'))

@app.route('/add_tag', methods=['POST'])
def add_tag():
    tag = request.form.get('tagSelected')
    task_index = int(request.form.get('taskIndex'))
    tasks[task_index][2] += [tag]

    update_db()

    return redirect(url_for('index'))

@app.route('/delete_tag', methods=['POST'])
def delete_tag():
    tag = request.form.get('tagSelected')
    task_index = int(request.form.get('taskIndex'))
    tasks[task_index][2].remove(tag)

    update_db()

    return redirect(url_for('index'))

@app.route('/create_tag', methods=['POST'])
def create_tag():
    tag = request.form.get('tagCreated')

    colour = request.form.get('newTagColour')
    tags[tag] = colour

    update_db()

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

    update_db()

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

    update_db()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0", port=env.get("PORT", 5000))
