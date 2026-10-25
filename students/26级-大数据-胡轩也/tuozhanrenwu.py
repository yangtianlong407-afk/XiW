allowed=["add","show","exit"]
def check(action):
    for action1 in allowed:
        if action==action1:
            return True
    return False
while True:
    action=input("输入动作:")
    if action == "exit":
        print("退出")
        break
    i=check(action)
    if i:
        print("允许")
    else:
        print("拒绝:这个动作没被授权")
