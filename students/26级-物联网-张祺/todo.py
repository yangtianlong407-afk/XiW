def add_task(tasks, t):
    tasks.append(t)


def show_tasks(tasks):
    if len(tasks) == 0:
        print("暂无任务")
        return

    for i in range(len(tasks)):
        print(str(i + 1) + ". " + tasks[i])


tasks = []

while True:
    print("1. 添加任务")
    print("2. 查看任务")
    print("3. 退出")
    choice = input("请选择：")

    if choice == "1":
        t = input("输入任务：")
        add_task(tasks, t)
        print("已添加：" + t)
    elif choice == "2":
        show_tasks(tasks)
    elif choice == "3":
        print("再见")
        break
    else:
        print("无效选择，请重新输入")
