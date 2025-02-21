from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tasks = {0:["task1",0],1:["task2",0],2:["task3",0]}
current_index = len(tasks)

@app.route('/')
def index():
    tasks_arg = {k: v for k, v in sorted(tasks.items(), key=lambda item: item[1][1])}
    return render_template('index.html', tasks=tasks_arg)

@app.route('/add', methods=['POST'])
def add_task():
    global current_index
    new_task = request.form.get('newTask')
    if new_task:
        tasks[current_index] = [new_task,0]
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
            tasks.pop(index)

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
