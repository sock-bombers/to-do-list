from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tasks = ["task1","task2","task3"]

@app.route('/')
def index():
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    new_task = request.form.get('newTask')
    if new_task:
        tasks.append(new_task)
    return redirect(url_for('index'))

@app.route('/complete', methods=['POST'])
def complete_tasks():
    completed_tasks = request.form.getlist('taskCheckbox')
    for index in map(int, completed_tasks):
        if 1 <= index <= len(tasks):
            tasks[index - 1] += " - Completed"
    return redirect(url_for('index'))

# Add a new route to handle task deletion
@app.route('/delete', methods=['POST'])
def delete_tasks():
    task_index = request.form.get('taskIndex')
    
    if task_index is not None:
        index = int(task_index)
        if 0 <= index < len(tasks):
            del tasks[index]

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
