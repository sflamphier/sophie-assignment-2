import time
# this is the job function in the background
def send_due_date_notification(task_title):
    time.sleep(5)
    print(f"Reminder: Task '{task_title}' is due soon!")
# we should see this printed about 5 seconds after creating a task that has a due date within 24 hours