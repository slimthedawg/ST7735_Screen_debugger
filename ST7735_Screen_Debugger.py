
# Author: Simon Chobot
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import time
import sys
import threading
import queue
import io
import contextlib
import sys
import select
import logging
import math

from flask import Flask, render_template, request

import ST7735 as TFT
import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI


app = Flask(__name__)
code_queue = queue.Queue()
screen_thread = None


################################### Variables ###################################

# Global variable to store the text
execution_result = ""
executed = False

# SPI Screen config 
WIDTH = 128
HEIGHT = 160
SPEED_HZ = 40_000_000 # 40MHz

# Raspberry Pi config
SPI_PORT = 0
SPI_DEVICE = 0
DC = 27
RST = 22

################################### Variables ###################################


# Used to stop any script that uses a while loop. To stop press "esc" in the terminal and press "Enter". Then you can "Run script" again in the browser
def is_data():
    return select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], [])



@app.route('/', methods=['GET', 'POST'])
async def index():
    global saved_text, executed, execution_result
    executed = False
    execution_result = ""

    if request.method == 'POST':
        saved_text = request.form['textfield']
        code_queue.put(saved_text)
        print("Applying script...")

    return render_template('index.html', saved_text=saved_text, execution_result=execution_result)
    



# Function to run in a separate thread
def screen_update_background():
    
    # Create TFT LCD display class.
    disp = TFT.ST7735(
        DC,
        rst=RST,
        spi=SPI.SpiDev(
            SPI_PORT,
            SPI_DEVICE,
            max_speed_hz=SPEED_HZ))
    
    # Initialize display.
    disp.begin()
    disp.clear((0, 0, 0))
    disp.clear((255, 255, 255))
    print("Screen Initialized.\n\n")

    i=0
    #Loop to await new script changes
    while True:
        global execution_result, executed
        code_to_execute = code_queue.get()  # Get the code from the queue
     
        if code_to_execute == "":
            time.sleep(1)

            execution_result = 'Empty.'
            code_queue.task_done()  # Signal that the task is done
            executed = True
            continue
        else:
            try:
                exec_output = io.StringIO()
                with contextlib.redirect_stdout(exec_output):
                    local_vars = { #Needs to be available for the script to handle the SPI screen
                        "disp": disp,
                        "WIDTH": WIDTH,
                        "HEIGHT": HEIGHT,
                    }
                    exec(code_to_execute, globals(), local_vars)
                execution_result = exec_output.getvalue() or 'Code executed successfully.'
                
            
            except Exception as e:
                execution_result = f'Error: {str(e)}'

            print("Script Applied.")
            print("Result:[\n" + execution_result + "\n]")
            code_queue.task_done()  # Signal that the task is done
            executed = True

    print("Thread out, not good.")
    logging.debug("Thread out, not good.")





################################### Main ###################################
if __name__ == '__main__':
    screen_thread = threading.Thread(target=screen_update_background)
    screen_thread.daemon = True
    screen_thread.start()

    app.run(host='0.0.0.0', port=5000, debug=True)



