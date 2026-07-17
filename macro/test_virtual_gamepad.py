import time

import vgamepad as vg


gamepad = vg.VX360Gamepad()
print("Virtual gamepad connected for 10 seconds.")
print("Open joy.cpl if you want to confirm that an Xbox 360 Controller appears.")
time.sleep(10)
gamepad.update()
print("Done.")
