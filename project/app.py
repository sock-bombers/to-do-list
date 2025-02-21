from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tasks = ["task1","task2","task3"]
tasks_checked = {"task1":0,"task2":0,"task3":0}

@app.route('/')
def index():
    return render_template('index.html', tasks={task:tasks_checked[task] for task in tasks})

@app.route('/add', methods=['POST'])
def add_task():
    new_task = request.form.get('newTask')
    if new_task:
        tasks.append(new_task)
        tasks_checked[new_task] = 0
    return redirect(url_for('index'))

@app.route('/complete', methods=['POST'])
def complete_tasks():
    completed_tasks = request.form.getlist('checkboxId')
    for index in map(int, completed_tasks):
        if 0 <= index <= len(tasks):
            if int(request.form["currentlyChecked"]):
                tasks_checked.pop(tasks[index])
                tasks[index] = tasks[index].replace(" - Completed","")
                tasks_checked[tasks[index]] = 0
            else:
                tasks_checked.pop(tasks[index])
                tasks[index] += " - Completed"
                tasks_checked[tasks[index]] = 1
    return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete_tasks():
    task_index = request.form.get('taskIndex')
    
    if task_index is not None:
        index = int(task_index)
        if 0 <= index < len(tasks):
            tasks_checked.pop(tasks.pop(index))

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
