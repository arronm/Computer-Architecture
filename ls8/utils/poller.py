import sys
import msvcrt
import queue
import threading

keyQueue = queue.SimpleQueue()

class KeyboardPoller(threading.Thread):
  def run(self):
    while True:
      x = msvcrt.kbhit()
      if x:
        key_pressed = 1
        key = ord(msvcrt.getch())
        keyQueue.put(key)

        if key == ord('q'):
          exit()
      else:
        key_pressed = 0
        key = None

if __name__ == "__main__":
  poller = KeyboardPoller()
  poller.start()

  while True:
    if not keyQueue.empty():
      char = keyQueue.get()
      if char == ord('q'):
        break
      print(chr(char))
  print('quit')
  