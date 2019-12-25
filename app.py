from flask import Flask, request, render_template
from collections import deque
import random
import json

app = Flask(__name__)

registered_numbers = set()   # all numbers registed to the service
banned_numbers     = set()   # numbers that cannot be registered
priority_queue     = deque() # queue of numbers that will be called next. If list is empty, use next_number_queue
next_number_queue  = deque() # queue of numbers to call next. if empty, fill it up from last_active_numbers and registered_numbers

try:
    with open("data_file.json", "r") as file:
        print('loading data from backup file')
        data = json.load(file)
        registered_numbers = set(data["registered_numbers"])
        banned_numbers = set(data["banned_numbers"])
except FileNotFoundError:
    print("Backup file does not exist. No data has been loaded.")

@app.route('/')
def hello():
    return render_template('register.html')

@app.route('/roulette')
def roulette():
    try:
        dectnumber = int(request.args.get('d', 0))
    except ValueError:
        return render_template('register.html', error = "invalid DECT number given")

    if dectnumber not in range(1, 99999):
        return render_template('register.html', error = "invalid DECT number given")

    if dectnumber in banned_numbers:
        return render_template('register.html', error = "this DECT number has been banned")


    # register number
    if dectnumber not in registered_numbers:
        registered_numbers.add(dectnumber)
        backup()
        # add newly registered numbers to priority_queue
        if dectnumber not in priority_queue:
            priority_queue.append(dectnumber)

    return render_template('roulette.html',
                           own_number = dectnumber,
                           partner_number = next_number(dectnumber),
                           priority = dectnumber in priority_queue,
                           active_users = len(registered_numbers))

@app.route('/unregister')
def unregister():
    try:
        dectnumber = int(request.args.get('d', 0))
    except ValueError:
        return render_template('register.html', error = "invalid DECT number given")

    if dectnumber not in range(1, 99999):
        return render_template('register.html', error = "invalid DECT number given")

    if dectnumber in registered_numbers:
        registered_numbers.remove(dectnumber)
        backup()

    while(priority_queue.count(dectnumber)):
        priority_queue.remove(dectnumber)

    while(next_number_queue.count(dectnumber)):
        next_number_queue.remove(dectnumber)

    return render_template('register.html', unregister = True)

@app.route('/admin')
def admin():
    try:
        number_to_ban = int(request.args.get('ban', 0))
        if number_to_ban != 0:
            banned_numbers.add(number_to_ban)
            backup()
    except ValueError:
        return render_template('admin.html', error = "invalid DECT number given", banned_numbers = sorted(banned_numbers))

    try:
        number_to_unban = int(request.args.get('unban', 0))
        if number_to_unban != 0:
            banned_numbers.remove(number_to_unban)
            backup()
    except (ValueError, KeyError):
        return render_template('admin.html', error = "invalid DECT number given", banned_numbers = sorted(banned_numbers))

    if "showusers" in request.args:
        return render_template('admin.html', banned_numbers = sorted(banned_numbers), registered_numbers = sorted(registered_numbers))

    return render_template('admin.html', banned_numbers = sorted(banned_numbers))


# ---- helper functions -----
def backup():
    with open("data_file.json", "w") as file:
        json.dump({
            "registered_numbers": list(registered_numbers),
            "banned_numbers": list(banned_numbers)
        }, file)


# determine next number to call
def next_number(own_number):
    if len(registered_numbers) <= 1:
        return '----'

    try:
        partner_number = priority_queue.popleft()
    except IndexError:
        # if priority_queue is empty, use next_number_queue
        try:
            partner_number = next_number_queue.popleft()
        except IndexError:
            # if next_number_queue is empty, fill next_number_queue
            registered_numbers_shuffled = list(registered_numbers)
            random.shuffle(registered_numbers_shuffled)
            next_number_queue.extend(registered_numbers_shuffled)
            partner_number = next_number_queue.popleft()

    if partner_number == own_number:
        partner_number = next_number(own_number)
    return partner_number
