tasks=[]
def add_task(tasks,task):
    tasks.append(task)
    print("已添加:",task)
def show_tasks(tasks):
    i=1
    for item in tasks:
        print(i,".",item)
        i=i+1
while True:
    print()
    print("1.添加任务")
    print("2.查看任务")
    print("3.退出")
    choice=input("请选择：")
    if choice=="1":
        new_task=input("输入任务：")
        add_task(tasks,new_task)
    elif choice=="2":
        show_tasks(tasks)
    elif choice=="3":
        print("再见")
        break