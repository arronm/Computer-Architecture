import sys
import msvcrt
import queue
import threading
stop_polling = False

class KeyboardPoller(threading.Thread):
  def run(self):
    global stop_polling
    while True:
      keypress = msvcrt.kbhit()
      if keypress:
        key = ord(msvcrt.getch())
        keyQueue.put(key)

      if stop_polling:
        exit()

if __name__ == "__main__":
  keyQueue = queue.SimpleQueue()
  stop_polling = False
  poller = KeyboardPoller()
  poller.start()

  while True:
    if not keyQueue.empty():
      char = keyQueue.get()
      if char == ord('q'):
        break
      print(chr(char))
  print('quit')
  stop_polling = True
  