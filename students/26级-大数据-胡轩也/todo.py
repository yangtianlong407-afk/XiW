def add_task(tasks, task):
    tasks.append(task)

def show_tasks(tasks):
    for i, t in enumerate(tasks, 1):
        print(f"{i}. {t}")


tasks = []
# 菜单只打印这一次！
print("1. 添加任务")
print("2. 查看任务")
print("3. 退出")

while True:
    choice = input("请选择：")
    if choice == "1":
        task = input("输入任务：")
        add_task(tasks, task)
        print(f"已添加：{task}")
    elif choice == "2":
        show_tasks(tasks)
    elif choice == "3":
        print("再见")
        break