print('start program')

from classes.program import Runner

receive = Runner('0.0.0.0', 32768)

print(receive.run())
