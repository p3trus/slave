"""This example shows a measurement routine for a custom magnetotransport setup
in the [P]hysical [P]roperties [M]easurement [S]ystem PPMS Model 6000.

"""
import visa

from slave.ppms import PPMS
from slave.sr830 import SR830

# Connect to the lockin amplifier and the ppms
lockin = SR830(visa.instrument('GPIB::10'))
ppms = PPMS(visa.instrument('GPIB::15'))

try:
    # Configure the lockin amplifier
    lockin.frequency = 22.45  # Use a detection frequency of 22.45 Hz
    lockin.amplitude = 5.0    # and an amplitude of 5 V.
    lockin.reserve = 'low'
    lockin.time_constant = 3

    # Set the ppms temperature to 10 K, cooling with a rate of 3 K per min.
    ppms.set_temperature(10, 3, wait_for_stability=True)
    # Now sweep slowly to avoid temperature instabilities.
    ppms.set_temperature(1.2, 0.5, wait_for_stability=True)
    # Set a magnetic field of 1 T at a rate of 0.2 T per minute and set the magnet
    # in persistent mode.
    #
    # Note: The PPMS uses Oersted instead of Tesla. 1 Oe = 0.1 mT.
    ppms.set_field(10000, 2000, mode='persistent', wait_for_stability=True)

    # Set the appropriate gain. (We're assuming the measured voltage decreases
    # with increasing temperature.
    lockin.auto_gain()

    # Define the measurement parameters
    parameters = [
        lambda: datetime.datetime.now(), # Get timestamp
        lambda: lockin.x,
        lambda: lockin.y,
        lambda: ppms.temperature,
    ]
    # Finally start the measurement, using the Measurement helper class as a
    # context manager (This automatically closes the measurement file).
    with Measurement('1.2K-300K_1T.dat', measure=parameters) as measurement:
        ppms.scan_temperature(measurement, 300, 0.5)
except Exception, e:
    # Catch possible errors and print a message.
    print 'An error occured:', e
finally:
    # Finally put the ppms in standby mode.
    ppms.shutdown()
