import time
from matplotlib import pyplot as pl 

# Start a log file
from instruments.tee import simple_log
simple_log(__file__)

# Now bring in the instrument factory
from instruments import factory

ps = factory.power_supply

ps.safety_voltage = 9.0 # ps.MAX_VOLTAGE
ps.volt_setpoint(channel = 1, voltage= 9.0)
ps.current_setpoint(channel = 1, amps=ps.MAX_CURRENT )
ps.output(channel = 1, state=ps.State.ON)
time.sleep(1.0)
print(f'OUTPUT = {ps.measure_voltage(channel=1)}')

print('''
# Run an oscope
''')
oscope = factory.oscilloscope   # Pick the first scope found

oscope.reset()

# Turn all channels off
for ch in range(oscope.NUM_ANA_CHAN):
    oscope.display(channel = ch, state = oscope.DisplayState.OFF)

# Turn on just the channels we need
oscope.display(channel = 1, state = oscope.DisplayState.ON)
oscope.display(channel = 2, state = oscope.DisplayState.ON)

# Set up trigger
oscope.probe_scale(channel = 1, nx = 10)
oscope.units(channel = 1, unit = oscope.Units.VOLT)
oscope.horizontal_scale(hdiv_sec = 0.000200)
oscope.vertical_scale(channel = 1, vdiv = 1.0)
oscope.horizontal_position(offset_sec = 0.000500)
oscope.trigger_edge(channel = 1, edgetype = oscope.TriggerEdges.RISING, level = 2.0)

oscope.run(trigsweep = oscope.TriggerSweeps.AUTO)

time.sleep(0.5)

measurements = oscope.measure(channel = 1, n = 1)

for m in measurements:
    print(f'{m:28s} : {measurements[m]} ')

oscope.stop()

v,t,preamble = oscope.data(channel = 1)
print(f'LENGTH = {len(v)}')
pl.plot(t,v)
pl.xlabel('Time (s)')
pl.ylabel('Voltage (V)')
pl.show()