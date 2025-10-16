from task import *

q = TCBQueue()
t1 = TCB(1, 255, 0, 0, "n")
t2 = TCB(2, 0, 255, 0, "r")
t3 = TCB(3, 0, 0, 255, "r")

q.push_back(t1)
q.push_back(t2)
q.push_back(t3)

print(len(q))

for t in q:
    print(f"Tarefa {t.id} ({t.state})")

removido = q.pop_front()
print("Removido:", removido.id)

print("Restam:", [t.id for t in q])
