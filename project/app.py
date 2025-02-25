from flask import Flask, render_template, request, redirect, url_for

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

#  id: [task_name, completed, [tag_names]]}
tasks = {
    0: ["Task 1", 0, ["Work", "Urgent"]],
    1: ["Task 2", 0, ["Personal"]],
    2: ["Task 3", 0, ["Urgent"]]
}

current_index = len(tasks)

@app.route('/')
def index():
    tasks_arg = {k: v for k, v in sorted(tasks.items(), key=lambda item: item[1][1])}
    return render_template('index.html', tasks=tasks_arg,tags=tags)

@app.route('/add', methods=['POST'])
def add_task():
    global current_index
    new_task = request.form.get('newTask') 
    if new_task:
        tasks[current_index] = [new_task, 0, []]
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

    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_tasks():
    task_index = request.form.get('taskIndex')
    
    if task_index is not None:
        index = int(task_index)
        if 0 <= index < current_index:
            tasks.pop(index,None)

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


if __name__ == '__main__':
    app.run(debug=True)
