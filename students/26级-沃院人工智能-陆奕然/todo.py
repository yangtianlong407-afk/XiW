tasks=[]
def add_task(tasks,task):
    tasks.append(task)

def show_tasks(tasks):
        for index,task in enumerate(tasks,start=1):
            print(f"{index}.{task}")
print("1.添加任务")
print("2.查看任务")
print("3.退出")
while True:
     choice=input("请选择：")
     if choice=="1":
        task=input("请输入任务：")
        add_task(tasks,task)
        print(f"已添加：{task}")
     elif choice=="2":   
          show_tasks(tasks)
     elif choice=="3":
          print("再见")
          break
     else:
            print("请输入1、2或3")