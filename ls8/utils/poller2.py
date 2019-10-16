import sys
import msvcrt
import queue
import threading

data_ready = threading.Event()
keyQueue = queue.SimpleQueue()

class KeyboardPoller(threading.Thread):
  def run(self):
    global key_pressed
    global key

    while True:
      x = msvcrt.kbhit()
      if x:
        key_pressed = 1
        key = ord(msvcrt.getch())
        keyQueue.put(key)

        if key == ord('q'):
          data_ready.set()
          exit()
        print(key)
      else:
        key_pressed = 0
        key = None
      data_ready.set()

  
if __name__ == "__main__":
  poller = KeyboardPoller()
  poller.start()
  while True:
    pressed = key
    # while not data_ready.isSet():
    while pressed is None:
      # print('main loop')
      if not keyQueue.empty():
        print(chr(keyQueue.get()))
      pass

    if pressed:
      char = chr(pressed)
      print(char)
      if chr(pressed) == 'q':
        break
  print('done')
  