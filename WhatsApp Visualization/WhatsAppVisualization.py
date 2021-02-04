import matplotlib.pyplot as plt

enc = 'utf-8'
f = open('_chat.txt', 'r', encoding=enc)
lines = f.readlines()

ratio =[]
users = []
data = []
status = []
msgTotal = 0

class Username:
    userCount = 0
    def __init__(self, name, messege):
        self.name = name
        self.messeges = []
        self.messeges.append(messege)
        self.msgNum = 1
        Username.userCount += 1
    
    def percent(self):
        num = self.msgNum
        percent = round((num/msgTotal) * 100, 2)
        return percent
    

for x in lines:
    try:
        msg = x.split(']',1)
        msgTime = msg[0]
        msgTime = msgTime.split(',',1)
        msgDate = msgTime[0]
        msgDate = msgDate.split('[',1)
        msgDate = msgDate[1]
        msgTime = msgTime[1]
        msgTime = msgTime[1:]
        msg = msg[1].split(':',1)
        sn = msg[0]
        sn = sn[1:]
        msg = msg[1]
        msg = msg[1:]
        msg = msg.lower()

        found = False
        msgFound = False

        if Username.userCount == 0:
            data.append(Username(sn, msg))
        else:
            for y in data:
                if y.name == sn:
                    found = True
                    for d in y.messeges:
                        if d == msg:
                            y.msgNum += 1
                            msgFound = True
                    if msgFound == False:
                        y.messeges.append(msg)
                        y.msgNum += 1
                    break
            if found == False:
                data.append(Username(sn, msg))
        msgTotal += 1
    except:
        pass

print('Output:')
print("Users:", Username.userCount)
for q in data:
    print(q.name, q.msgNum)
    if q.msgNum > 1:
        users.append(q.name)
        ratio.append(q.percent())
print("Total:", msgTotal)
print(ratio)
print(users)

fig1, ax1 = plt.subplots()
ax1.pie(ratio, labels=users, autopct='%1.1f%%', shadow=True, startangle=90, pctdistance=1.1, labeldistance=1.2)
plt.legend(labels = users, loc="best")
ax1.axis('equal')
plt.show()