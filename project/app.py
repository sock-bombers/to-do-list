from flask import Flask, render_template, request, redirect, url_for
import time

app = Flask(__name__)

def colour_intensity(hex):
  hex = hex.replace("#","")
  return sum(tuple(int(hex[i:i+2], 16) for i in (0, 2, 4)))/3
app.jinja_env.globals.update(colour_intensity = colour_intensity)

tags = {
    "Work": "#aae364",
    "Personal": "#4e76d4",
    "Urgent": "#cf0000",
}

filtered_tag = ""

#  id: [task_name, completed, [tag_names], recently_added]}
tasks = {
    0: ["Task 1", 0, ["Work", "Urgent"], 0],
    1: ["Task 2", 0, ["Personal"], 0],
    2: ["Task 3", 0, ["Urgent"], 0]
}

def reset_recently_added(task):
  tasks[task][3] = 0
app.jinja_env.globals.update(reset_recently_added = reset_recently_added)

current_index = len(tasks)

@app.route('/')
def index():
    if filtered_tag == "":
        checked_tasks = {k: v for k, v in reversed({k: v for k, v in tasks.items() if v[1] == 1}.items())}
        unchecked_tasks = {k: v for k, v in reversed({k: v for k, v in tasks.items() if v[1] == 0}.items())}
    else:
        checked_tasks = {k: v for k, v in reversed({k: v for k, v in tasks.items() if v[1] == 1 and filtered_tag in v[2]}.items())}
        unchecked_tasks = {k: v for k, v in reversed({k: v for k, v in tasks.items() if v[1] == 0 and filtered_tag in v[2]}.items())}
    tasks_arg = unchecked_tasks.copy()
    tasks_arg.update(checked_tasks)
    return render_template('index.html', tasks=tasks_arg,tags=tags,filtered_tag=filtered_tag)

@app.route('/add', methods=['POST'])
def add_task():
    global current_index
    new_task = request.form.get('newTask') 
    if new_task:
        tasks[current_index] = [new_task, 0, [], 1]
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


if __name__ == '__main__':
    app.run(debug=True)
