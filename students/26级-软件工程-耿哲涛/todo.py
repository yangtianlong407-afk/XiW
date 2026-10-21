tasks = []

def add_task(tasks,task):
    tasks.append(task)

def show_tasks(tasks):
    n=1
    for t in tasks:
        print(str(n)+"."+t)
        n=n+1

while True:
    print("1.添加任务")
    print("2.查看任务")
    print("3.退出")

    choice = input("请选择：")

    if choice=="1":
        task=input("输入任务：")
        add_task(tasks,task)
        print("已添加："+task)
    elif choice=="2":
        show_tasks(tasks)
    else:
        print("再见")
        break