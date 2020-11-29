import csv
import time
from matplotlib import pyplot as pl 

# Start a log file
from instruments.tee import simple_log
simple_log(__file__)

# Now bring in the instrument factory
from instruments import factory

try:
    ps = factory.power_supply
    ps.verbose = True

    MAX_V = 5.0

    ps.safety_voltage = MAX_V
    ps.volt_setpoint(channel = 1, voltage= MAX_V)
    ps.current_setpoint(channel = 1, amps=ps.MAX_CURRENT )
    ps.output(channel = 1, state=ps.State.ON)

    time.sleep(1.0)
    ps.measure_voltage(channel=1)

    # Run an oscope
    oscope = factory.oscilloscope   # Pick the first scope found
    oscope.verbose = True

    oscope.reset()

    # Turn four channels with same veritical scaling
    for ch in range(1,5):
        oscope.display(channel = ch, state = oscope.DisplayState.ON)
        oscope.probe_scale(channel = ch, nx = 10)
        oscope.units(channel = ch, unit = oscope.Units.VOLT)
        oscope.vertical_scale(channel = ch, vdiv = 1.0)
        oscope.vertical_position(channel = ch, offset = 3.0)

    # Set up trigger
    oscope.horizontal_scale(hdiv_sec = 0.0500)
    oscope.horizontal_position(offset_sec = -0.250)
    oscope.trigger_edge(channel = 1, edgetype = oscope.TriggerEdges.RISING, level = MAX_V/2.0)

    oscope.run(trigsweep = oscope.TriggerSweeps.AUTO)

    oscope.wait_for_trigger_status(trigger_status = oscope.TriggerStatus.TRIGGERED, timeout_sec = 10.0)

    measurements = oscope.measure(channel = 1, n = 1, delay_sec = 5.0)

    for m in measurements:
        print(f'{m:28s} : {measurements[m]} ')
    
    oscope.wait_for_trigger_status(trigger_status = oscope.TriggerStatus.TRIGGERED, timeout_sec = 10.0)

    oscope.stop()
    ps.output(channel = 1, state=ps.State.OFF)

    v_output,t_output,_ = oscope.data(channel = 1)
    v_inv_input, t_inv_input, _ = oscope.data(channel = 2)
    v_ninv_input, t_ninv_input, _ = oscope.data(channel = 3)
    v_ref, t_ref, _ = oscope.data(channel = 4)

    oscope.screen_capture('.\ethan_screen_capture.png')

    with open('.\ethan_data.csv',mode = 'w',newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['t_output','v_output','v_inv_input','v_ninv_input','v_ref'])
        for i in range(len(t_output)):
            writer.writerow([t_output[i],v_output[i],v_inv_input[i],v_ninv_input[i],v_ref[i]])
    
    pl.plot(t_output,v_output, t_inv_input, v_inv_input, t_ninv_input, v_ninv_input, t_ref, v_ref)
    pl.title('Bi-stable Oscillator Performance')
    pl.xlabel('Time (s)')
    pl.ylabel('Voltage (V)')
    pl.legend(['Output', 'Inverting Input','Non-Inv Input','Reference'])
    pl.grid()
    pl.ylim((0,MAX_V))
    pl.savefig('.\ethan_plot.png')
finally:
    oscope.stop()
    ps.output(channel = 1, state=ps.State.OFF)
