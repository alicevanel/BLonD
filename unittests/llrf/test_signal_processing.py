# coding: utf8
# Copyright 2014-2017 CERN. This software is distributed under the
# terms of the GNU General Public Licence version 3 (GPL Version 3),
# copied verbatim in the file LICENCE.md.
# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.
# Project website: http://blond.web.cern.ch/

"""
Unittest for llrf.filters

:Authors: **Helga Timko**
"""

import unittest
import numpy as np
from scipy.constants import e

from blond.llrf.signal_processing import moving_average, modulator
from blond.llrf.signal_processing import polar_to_cartesian, cartesian_to_polar
from blond.llrf.signal_processing import comb_filter, low_pass_filter
from blond.llrf.signal_processing import rf_beam_current, feedforward_filter
from blond.llrf.signal_processing import feedforward_filter_TWC3, \
    feedforward_filter_TWC4, feedforward_filter_TWC5

from blond.llrf.impulse_response import SPS3Section200MHzTWC, \
    SPS4Section200MHzTWC, SPS5Section200MHzTWC

from blond.input_parameters.ring import Ring
from blond.beam.beam import Beam, Proton
from blond.beam.profile import Profile, CutOptions
from blond.beam.distributions import bigaussian
from blond.input_parameters.rf_parameters import RFStation

class TestIQ(unittest.TestCase):

    # Run before every test
    def setUp(self, f_rf=200.1e6, T_s=5e-10, n=1000):

        self.f_rf = f_rf  # initial frequency in Hz
        self.T_s = T_s  # sampling time
        self.n = n  # number of points

    # Run after every test
    def tearDown(self):

        del self.f_rf
        del self.T_s
        del self.n

    def test_1(self):

        # Define signal in range (-pi, pi)
        phases = np.pi*(np.fmod(2*np.arange(self.n)*self.f_rf*self.T_s, 2) - 1)
        signal = np.cos(phases) + 1j*np.sin(phases)
        # From IQ to polar
        amplitude, phase = cartesian_to_polar(signal)

        # Drop some digits to avoid rounding errors
        amplitude = np.around(amplitude, 12)
        phase = np.around(phase, 12)
        phases = np.around(phases, 12)
        self.assertSequenceEqual(amplitude.tolist(), np.ones(self.n).tolist(),
            msg="In TestIQ test_1, amplitude is not correct")
        self.assertSequenceEqual(phase.tolist(), phases.tolist(),
            msg="In TestIQ test_1, phase is not correct")

    def test_2(self):

        # Define signal in range (-pi, pi)
        phase = np.pi*(np.fmod(2*np.arange(self.n)*self.f_rf*self.T_s, 2) - 1)
        amplitude = np.ones(self.n)
        # From polar to IQ
        signal = polar_to_cartesian(amplitude, phase)

        # Drop some digits to avoid rounding errors
        signal_real = np.around(signal.real, 12)
        signal_imag = np.around(signal.imag, 12)
        theor_real = np.around(np.cos(phase), 12)  # what it should be
        theor_imag = np.around(np.sin(phase), 12)  # what it should be
        self.assertSequenceEqual(signal_real.tolist(), theor_real.tolist(),
            msg="In TestIQ test_2, real part is not correct")
        self.assertSequenceEqual(signal_imag.tolist(), theor_imag.tolist(),
            msg="In TestIQ test_2, imaginary part is not correct")

    def test_3(self):

        # Define signal in range (-pi, pi)
        phase = np.pi*(np.fmod(2*np.arange(self.n)*self.f_rf*self.T_s, 2) - 1)
        amplitude = np.ones(self.n)
        # Forwards and backwards transform
        signal = polar_to_cartesian(amplitude, phase)
        amplitude_new, phase_new = cartesian_to_polar(signal)

        # Drop some digits to avoid rounding errors
        phase = np.around(phase, 11)
        amplitude = np.around(amplitude, 11)
        amplitude_new = np.around(amplitude_new, 11)
        phase_new = np.around(phase_new, 11)
        self.assertSequenceEqual(phase.tolist(), phase_new.tolist(),
                                 msg="In TestIQ test_3, phase is not correct")
        self.assertSequenceEqual(amplitude.tolist(), amplitude_new.tolist(),
            msg="In TestIQ test_3, amplitude is not correct")

    def test_4(self):

        # Define signal in range (-pi, pi)
        phase = np.pi*(np.fmod(2*np.arange(self.n)*self.f_rf*self.T_s, 2) - 1)
        signal = np.cos(phase) + 1j*np.sin(phase)
        # Forwards and backwards transform
        amplitude, phase = cartesian_to_polar(signal)
        signal_new = polar_to_cartesian(amplitude, phase)

        # Drop some digits to avoid rounding errors
        signal_real = np.around(signal.real, 11)
        signal_imag = np.around(signal.imag, 11)
        signal_real_2 = np.around(np.real(signal_new), 11)
        signal_imag_2 = np.around(np.imag(signal_new), 11)
        self.assertSequenceEqual(signal_real.tolist(), signal_real_2.tolist(),
            msg="In TestIQ test_4, real part is not correct")
        self.assertSequenceEqual(signal_imag.tolist(), signal_imag_2.tolist(),
            msg="In TestIQ test_4, imaginary part is not correct")


class TestModulator(unittest.TestCase):

    def setUp(self, f_rf=200.1e6, f_0=200.222e6, T_s=5e-10, n=1000):
        self.f_rf = f_rf    # initial frequency in Hz
        self.f_0 = f_0      # final frequency in Hz
        self.T_s = T_s      # sampling time
        self.n = n          # number of points

    def test_v1(self):

        # Forwards and backwards transformation of a sine wave
        signal = np.cos(2*np.pi*np.arange(self.n)*self.f_rf*self.T_s) \
            + 1j*np.sin(2*np.pi*np.arange(self.n)*self.f_rf*self.T_s)
        signal_1 = modulator(signal, self.f_rf, self.f_0, self.T_s)
        signal_2 = modulator(signal_1, self.f_0, self.f_rf, self.T_s)

        # Drop some digits to avoid rounding errors
        signal = np.around(signal, 12)
        signal_2 = np.around(signal_2, 12)
        self.assertSequenceEqual(signal.tolist(), signal_2.tolist(),
            msg="In TestModulator, initial and final signals do not match")

    def test_v2(self):

        signal = np.array([42])

        with self.assertRaises(RuntimeError,
            msg="In TestModulator, no exception for wrong signal length"):

            modulator(signal, self.f_rf, self.f_0, self.T_s)


class TestRFCurrent(unittest.TestCase):

    def setUp(self):

        C = 2*np.pi*1100.009        # Ring circumference [m]
        gamma_t = 18.0              # Gamma at transition
        alpha = 1/gamma_t**2        # Momentum compaction factor
        p_s = 25.92e9               # Synchronous momentum at injection [eV]

        N_m = 1e5                   # Number of macro-particles for tracking
        N_b = 1.0e11                # Bunch intensity [ppb]

        # Set up machine parameters
        self.ring = Ring(C, alpha, p_s, Proton(), n_turns=1)
        self.rf = RFStation(self.ring, 4620, 4.5e6, 0)

        # RF-frequency at which to compute beam current
        self.omega = 2*np.pi*200.222e6
        
        # Create Gaussian beam
        self.beam = Beam(self.ring, N_m, N_b)
        self.profile = Profile(self.beam, CutOptions=CutOptions(cut_left=-1e-9,
            cut_right=6e-9, n_slices=100))

    # Test charge distribution with analytic functions
    # Compare with theoretical value
    def test_1(self):

        t = self.profile.bin_centers
        self.profile.n_macroparticles \
            = 2600*np.exp(-(t-2.5e-9)**2 / (2*0.5e-9)**2)

        rf_current = rf_beam_current(self.profile, self.omega,
                                     self.ring.t_rev[0], lpf=False)

        rf_current_real = np.around(rf_current.real, 12)
        rf_current_imag = np.around(rf_current.imag, 12)

        rf_theo_real = 2*self.beam.ratio*self.profile.Beam.Particle.charge*e\
            * 2600*np.exp(-(t-2.5e-9)**2/(2*0.5*1e-9)**2)\
            * np.cos(self.omega*t)
        rf_theo_real = np.around(rf_theo_real, 12)

        rf_theo_imag = 2*self.beam.ratio*self.profile.Beam.Particle.charge*e\
            * 2600*np.exp(-(t-2.5e-9)**2/(2*0.5*1e-9)**2)\
            * np.sin(self.omega*t)
        rf_theo_imag = np.around(rf_theo_imag, 12)

        self.assertListEqual(rf_current_real.tolist(), rf_theo_real.tolist(),
            msg="In TestRfCurrent test_1, mismatch in real part of RF current")
        self.assertListEqual(rf_current_imag.tolist(), rf_theo_imag.tolist(),
            msg="In TestRfCurrent test_1, mismatch in real part of RF current")

    # Test charge distribution of a bigaussian profile, without LPF
    # Compare to simulation data
    def test_2(self):

        bigaussian(self.ring, self.rf, self.beam, 3.2e-9/4, seed=1234,
                   reinsertion=True)
        self.profile.track()

        rf_current = rf_beam_current(self.profile, self.omega,
                                     self.ring.t_rev[0], lpf=False)

        Iref_real = np.array(
                [0.00000000e+00, 0.00000000e+00, 0.00000000e+00,
                 0.00000000e+00, 4.17276535e-13, 4.58438681e-13,
                 2.48023976e-13, 5.29812878e-13, 2.79735891e-13,
                 0.00000000e+00, 1.21117141e-12, 9.32525023e-13,
                 3.16481489e-13, 6.39337176e-13, 0.00000000e+00,
                 0.00000000e+00, 4.08671434e-12, 4.92294314e-12,
                 6.56965575e-12, 1.06279981e-11, 1.36819774e-11,
                 2.16648778e-11, 3.09847740e-11, 3.52971849e-11,
                 4.70378842e-11, 4.53538351e-11, 4.87255679e-11,
                 5.36705228e-11, 5.13609263e-11, 4.32833543e-11,
                 3.41417624e-11, 1.57452091e-11, -1.09005668e-11,
                 -4.60465929e-11, -9.12872553e-11, -1.48257171e-10,
                 -2.08540597e-10, -2.77630608e-10, -3.72157667e-10,
                 -4.56272786e-10, -5.57978710e-10, -6.46554672e-10,
                 -7.48006839e-10, -8.21493943e-10, -9.37522966e-10,
                 -1.03729659e-09, -1.06159943e-09, -1.08434837e-09,
                 -1.15738771e-09, -1.17887328e-09, -1.17146946e-09,
                 -1.10964397e-09, -1.10234198e-09, -1.08852433e-09,
                 -9.85866185e-10, -9.11727492e-10, -8.25604179e-10,
                 -7.34122902e-10, -6.47294094e-10, -5.30372699e-10,
                 -4.40357820e-10, -3.61273445e-10, -2.76871612e-10,
                 -2.02227691e-10, -1.45430219e-10, -8.88675652e-11,
                 -4.28984525e-11, -8.85451321e-12,  1.79026289e-11,
                 3.48384211e-11,  4.50190278e-11, 5.62413467e-11,
                 5.27322593e-11,  4.98163111e-11, 4.83288193e-11,
                 4.18200848e-11,  3.13334266e-11, 2.44082106e-11,
                 2.12572803e-11,  1.37397871e-11, 1.00879346e-11,
                 7.78502206e-12,  4.00790815e-12, 2.51830412e-12,
                 1.91301488e-12,  0.00000000e+00, 9.58518921e-13,
                 3.16123806e-13,  1.24116545e-12, 1.20821671e-12,
                 5.82952178e-13,  8.35917228e-13, 5.27285250e-13,
                 4.93205915e-13,  0.00000000e+00, 2.06937011e-13,
                 1.84618141e-13,  1.60868490e-13, 0.00000000e+00,
                 1.09822742e-13])
        
        I_real = np.around(rf_current.real, 14) # round
        Iref_real = np.around(Iref_real, 14)
        
        self.assertSequenceEqual(I_real.tolist(), Iref_real.tolist(),
            msg="In TestRFCurrent test_2, mismatch in real part of RF current")
        
        Iref_imag = np.array([
                0.00000000e+00,   0.00000000e+00,   0.00000000e+00,
                0.00000000e+00,  -4.86410815e-13,  -4.47827158e-13,
                -2.02886432e-13,  -3.60573852e-13,  -1.56290206e-13,
                0.00000000e+00,  -4.19433613e-13,  -2.33465744e-13,
                -5.01823105e-14,  -4.43075921e-14,   0.00000000e+00,
                0.00000000e+00,   8.07144709e-13,   1.43192280e-12,
                2.55659168e-12,   5.25480064e-12,   8.33669524e-12,
                1.59729353e-11,   2.73609511e-11,   3.71844853e-11,
                5.92134758e-11,   6.87376280e-11,   9.02226570e-11,
                1.24465616e-10,   1.55478762e-10,   1.84035433e-10,
                2.37241518e-10,   2.86677989e-10,   3.28265272e-10,
                3.77882012e-10,   4.29727720e-10,   4.83759029e-10,
                5.13978173e-10,   5.41841031e-10,   5.91537968e-10,
                6.00658643e-10,   6.13928028e-10,   5.96367636e-10,
                5.76920099e-10,   5.25297875e-10,   4.89104065e-10,
                4.29776324e-10,   3.33901906e-10,   2.38690921e-10,
                1.49673305e-10,   4.78223853e-11,  -5.57081558e-11,
                -1.51374774e-10,  -2.50724894e-10,  -3.50731761e-10,
                -4.16547058e-10,  -4.83765618e-10,  -5.36075032e-10,
                -5.74421794e-10,  -6.05459147e-10,  -5.91794283e-10,
                -5.88179055e-10,  -5.83222843e-10,  -5.49774151e-10,
                -5.08571646e-10,  -4.86623358e-10,  -4.33179012e-10,
                -3.73737133e-10,  -3.37622742e-10,  -2.89119788e-10,
                -2.30660798e-10,  -1.85597518e-10,  -1.66348322e-10,
                -1.19981335e-10,  -9.07232680e-11,  -7.21467862e-11,
                -5.18977454e-11,  -3.25510912e-11,  -2.12524272e-11,
                -1.54447488e-11,  -8.24107056e-12,  -4.90052047e-12,
                -2.96720377e-12,  -1.13551262e-12,  -4.79152734e-13,
                -1.91861296e-13,   0.00000000e+00,   7.31481456e-14,
                5.23883203e-14,   3.19951675e-13,   4.27870459e-13,
                2.66236636e-13,   4.74712082e-13,   3.64260145e-13,
                4.09222572e-13,   0.00000000e+00,   2.44654594e-13,
                2.61906356e-13,   2.77128356e-13,   0.00000000e+00,
                3.01027843e-13])
        
        I_imag = np.around(rf_current.imag, 14) # round
        Iref_imag = np.around(Iref_imag, 14)
        
        self.assertSequenceEqual(I_imag.tolist(), Iref_imag.tolist(),
            msg="In TestRFCurrent test_2, mismatch in imaginary part of"
            + " RF current")
    
    # Test charge distribution of a bigaussian profile, with LPF
    # Compare to simulation data
    def test_3(self):
        
        bigaussian(self.ring, self.rf, self.beam, 3.2e-9/4, seed=1234,
                   reinsertion=True)
        self.profile.track()
        self.assertEqual(len(self.beam.dt), np.sum(self.profile.n_macroparticles), "In" +
            " TestBeamCurrent: particle number mismatch in Beam vs Profile")

        # RF current calculation with low-pass filter
        rf_current = rf_beam_current(self.profile, self.omega,
                                     self.ring.t_rev[0], lpf=True)

        Iref_real = np.array([-7.1511849777e-12, -7.1512648914e-12, -7.1513422943e-12, -7.1514172380e-12,
                            -7.1514897737e-12, -7.1515599522e-12, -7.1516278240e-12, -7.1516934391e-12,
                            -7.1517568472e-12, -7.1518180976e-12, -7.1518772391e-12, -7.1519343203e-12,
                            -7.1519893891e-12, -7.1520424932e-12, -7.1520936796e-12, -7.1521429951e-12,
                            -7.1521904858e-12, -7.1522361976e-12, -7.1522801757e-12, -7.1523224649e-12,
                            -7.1523631094e-12, -7.1524021531e-12, -7.1524396391e-12, -7.1524756102e-12,
                            -7.1525101085e-12, -7.1525431759e-12, -7.1525748533e-12, -7.1526051813e-12,
                            -7.1526341999e-12, -7.1526619485e-12, -7.1526884660e-12, -7.1527137906e-12,
                            -7.1527379600e-12, -7.1527610114e-12, -7.1527829811e-12, -7.1528039051e-12,
                            -7.1528238187e-12, -7.1528427564e-12, -7.1528607524e-12, -7.1528778400e-12,
                            -7.1528940521e-12, -7.1529094207e-12, -7.1529239774e-12, -7.1529377531e-12,
                            -7.1529507780e-12, -7.1529630816e-12, -7.1529746930e-12, -7.1529856403e-12,
                            -7.1529959513e-12, -7.1530056528e-12, -7.1530147714e-12, -7.1530233325e-12,
                            -7.1530313612e-12, -7.1530388818e-12, -7.1530459182e-12, -7.1530524933e-12,
                            -7.1530586294e-12, -7.1530643485e-12, -7.1530696714e-12, -7.1530746188e-12,
                            -7.1530792103e-12, -7.1530834652e-12, -7.1530874019e-12, -7.1530910384e-12,
                            -7.1530943918e-12, -7.1530974789e-12, -7.1531003156e-12, -7.1531029173e-12,
                            -7.1531052989e-12, -7.1531074745e-12, -7.1531094576e-12, -7.1531112614e-12,
                            -7.1531128983e-12, -7.1531143801e-12, -7.1531157181e-12, -7.1531169232e-12,
                            -7.1531180054e-12, -7.1531189746e-12, -7.1531198399e-12, -7.1531206099e-12,
                            -7.1531212929e-12, -7.1531218966e-12, -7.1531224281e-12, -7.1531228942e-12,
                            -7.1531233014e-12, -7.1531236554e-12, -7.1531239617e-12, -7.1531242255e-12,
                            -7.1531244515e-12, -7.1531246439e-12, -7.1531248068e-12, -7.1531249437e-12,
                            -7.1531250581e-12, -7.1531251528e-12, -7.1531252307e-12, -7.1531252941e-12,
                            -7.1531253453e-12, -7.1531253862e-12, -7.1531254184e-12, -7.1531254434e-12])

        np.testing.assert_allclose(rf_current.real, Iref_real, rtol=1e-7,
            atol=0, err_msg="In TestRFCurrent test_3, mismatch in real part of RF current")

        Iref_imag = np.array([-2.1797190538e-12, -2.1796751508e-12, -2.1796326846e-12, -2.1795916238e-12,
                            -2.1795519372e-12, -2.1795135939e-12, -2.1794765633e-12, -2.1794408150e-12,
                            -2.1794063189e-12, -2.1793730453e-12, -2.1793409646e-12, -2.1793100476e-12,
                            -2.1792802656e-12, -2.1792515898e-12, -2.1792239921e-12, -2.1791974445e-12,
                            -2.1791719194e-12, -2.1791473895e-12, -2.1791238279e-12, -2.1791012079e-12,
                            -2.1790795034e-12, -2.1790586883e-12, -2.1790387372e-12, -2.1790196249e-12,
                            -2.1790013264e-12, -2.1789838175e-12, -2.1789670739e-12, -2.1789510719e-12,
                            -2.1789357882e-12, -2.1789211998e-12, -2.1789072841e-12, -2.1788940190e-12,
                            -2.1788813826e-12, -2.1788693535e-12, -2.1788579106e-12, -2.1788470334e-12,
                            -2.1788367017e-12, -2.1788268955e-12, -2.1788175955e-12, -2.1788087826e-12,
                            -2.1788004382e-12, -2.1787925441e-12, -2.1787850824e-12, -2.1787780359e-12,
                            -2.1787713874e-12, -2.1787651204e-12, -2.1787592188e-12, -2.1787536666e-12,
                            -2.1787484487e-12, -2.1787435500e-12, -2.1787389559e-12, -2.1787346523e-12,
                            -2.1787306255e-12, -2.1787268621e-12, -2.1787233492e-12, -2.1787200742e-12,
                            -2.1787170249e-12, -2.1787141897e-12, -2.1787115571e-12, -2.1787091161e-12,
                            -2.1787068562e-12, -2.1787047670e-12, -2.1787028388e-12, -2.1787010621e-12,
                            -2.1786994277e-12, -2.1786979269e-12, -2.1786965513e-12, -2.1786952928e-12,
                            -2.1786941438e-12, -2.1786930968e-12, -2.1786921449e-12, -2.1786912814e-12,
                            -2.1786904998e-12, -2.1786897941e-12, -2.1786891586e-12, -2.1786885878e-12,
                            -2.1786880764e-12, -2.1786876198e-12, -2.1786872132e-12, -2.1786868523e-12,
                            -2.1786865331e-12, -2.1786862518e-12, -2.1786860047e-12, -2.1786857886e-12,
                            -2.1786856004e-12, -2.1786854373e-12, -2.1786852964e-12, -2.1786851755e-12,
                            -2.1786850722e-12, -2.1786849845e-12, -2.1786849105e-12, -2.1786848484e-12,
                            -2.1786847967e-12, -2.1786847540e-12, -2.1786847190e-12, -2.1786846906e-12,
                            -2.1786846677e-12, -2.1786846495e-12, -2.1786846352e-12, -2.1786846241e-12])

        np.testing.assert_allclose(rf_current.imag, Iref_imag, rtol=1e-7,
            atol=0, err_msg="In TestRFCurrent test_3, mismatch in imaginary part of RF current")

    # Test RF beam current on coarse grid integrated from fine grid
    # Compare to simulation data for peak RF current
    def test_4(self):

        # Create a batch of 100 equal, short bunches
        bunches = 100
        T_s = 5*self.rf.t_rev[0]/self.rf.harmonic[0, 0]
        N_m = int(1e5)
        N_b = 2.3e11
        bigaussian(self.ring, self.rf, self.beam, 0.1e-9, seed=1234,
                   reinsertion=True)
        beam2 = Beam(self.ring, bunches*N_m, bunches*N_b)
        bunch_spacing = 5*self.rf.t_rf[0, 0]
        buckets = 5*bunches
        for i in range(bunches):
            beam2.dt[i*N_m:(i+1)*N_m] = self.beam.dt + i*bunch_spacing
            beam2.dE[i*N_m:(i+1)*N_m] = self.beam.dE
        profile2 = Profile(beam2, CutOptions=CutOptions(cut_left=0,
            cut_right=bunches*bunch_spacing, n_slices=1000*buckets))
        profile2.track()

        tot_charges = np.sum(profile2.n_macroparticles)/\
                     beam2.n_macroparticles*beam2.intensity
        self.assertAlmostEqual(tot_charges, 2.3000000000e+13, 9)

        # Calculate fine- and coarse-grid RF current
        rf_current_fine, rf_current_coarse = rf_beam_current(profile2,
            self.rf.omega_rf[0, 0], self.ring.t_rev[0], lpf=False,
            downsample={'Ts': T_s, 'points': self.rf.harmonic[0, 0]/5})
        rf_current_coarse /= T_s

        # Peak RF current on coarse grid
        peak_rf_current = np.max(np.absolute(rf_current_coarse))
        self.assertAlmostEqual(peak_rf_current, 2.9285808008, 7)


class TestComb(unittest.TestCase):

    def test_1(self):
        y = np.random.rand(42)

        self.assertListEqual(y.tolist(), comb_filter(y, y, 15/16).tolist(),
            msg="In TestComb test_1, filtered signal not correct")

    def test_2(self):

        t = np.arange(0, 2*np.pi, 2*np.pi/120)
        y = np.cos(t)
        # Shift cosine by quarter period
        x = np.roll(y, int(len(t)/4))

        # Drop some digits to avoid rounding errors
        result = np.around(comb_filter(y, x, 0.5), 12)
        result_theo = np.around(np.sin(np.pi/4 + t)/np.sqrt(2), 12)

        self.assertListEqual(result.tolist(), result_theo.tolist(),
            msg="In TestComb test_2, filtered signal not correct")


class TestLowPass(unittest.TestCase):

    def test_1(self):
        # Example based on SciPy.org filtfilt
        t = np.linspace(0, 1.0, 2001)
        xlow = np.sin(2 * np.pi * 5 * t)
        xhigh = np.sin(2 * np.pi * 250 * t)
        x = xlow + xhigh

        y = low_pass_filter(x, cutoff_frequency=1/8)

        # Test for difference between filtered signal and xlow;
        # using signal.butter(8, 0.125) and filtfilt(b, a, x, padlen=15)
        # from the SciPy documentation of filtfilt gives the stated
        # value 9.10862958....e-6
        self.assertAlmostEqual(np.abs(y - xlow).max(), 0.0230316365,
                               places=10)


class TestMovingAverage(unittest.TestCase):

    # Run before every test
    def setUp(self, N=3, x_prev=None):
        self.x = np.array([0, 3, 6, 3, 0, 3, 6, 3, 0], dtype=float)
        self.y = moving_average(self.x, N, x_prev)

    # Run after every test
    def tearDown(self):

        del self.x
        del self.y

    def test_1(self):

        self.setUp(N=3)
        self.assertEqual(len(self.x), len(self.y) + 3 - 1,
            msg="In TestMovingAverage, test_1: wrong array length")
        self.assertSequenceEqual(self.y.tolist(),
            np.array([3, 4, 3, 2, 3, 4, 3], dtype=float).tolist(),
            msg="In TestMovingAverage, test_1: arrays differ")

    def test_2(self):

        self.setUp(N=4)
        self.assertEqual(len(self.x), len(self.y) + 4 - 1,
            msg="In TestMovingAverage, test_2: wrong array length")
        self.assertSequenceEqual(self.y.tolist(),
                                 np.array([3, 3, 3, 3, 3, 3],
                                          dtype=float).tolist(),
            msg="In TestMovingAverage, test_2: arrays differ")

    def test_3(self):

        self.setUp(N=3, x_prev=np.array([0, 3]))
        self.assertEqual(len(self.x), len(self.y),
            msg="In TestMovingAverage, test_3: wrong array length")
        self.assertSequenceEqual(self.y.tolist(),
            np.array([1, 2, 3, 4, 3, 2, 3, 4, 3], dtype=float).tolist(),
            msg="In TestMovingAverage, test_3: arrays differ")


class TestFeedforwardFilter(unittest.TestCase):

    # Run before every test
    def setUp(self):

        # Ring and RF definitions
        ring = Ring(2*np.pi*1100.009, 1/18**2, 25.92e9, Particle=Proton())
        rf = RFStation(ring, [4620], [4.5e6], [0.], n_rf=1)
        self.T_s = 5*rf.t_rf[0, 0]

    def test_1(self):

        # Modified filling time to match reference case
        TWC = SPS3Section200MHzTWC()
        TWC.tau = 420e-9
        filter, n_taps, n_filling, n_fit = feedforward_filter(TWC, 4/125*1e-6,
            debug=False, taps=31, opt_output=True)
        self.assertEqual(n_taps, 31,
            msg="In TestFeedforwardFilter, test_1: n_taps incorrect")
        self.assertEqual(n_filling, 13,
            msg="In TestFeedforwardFilter, test_1: n_filling incorrect")
        self.assertEqual(n_fit, 44,
            msg="In TestFeedforwardFilter, test_1: n_fit incorrect")

        filter_ref = np.array(
            [-0.0227533635, 0.0211514102, 0.0032929202, -0.0026111554,
              0.0119559316, 0.0043905603, 0.0043905603, 0.0040101282,
             -0.0241480816, -0.0237676496, 0.0043905603, 0.0043905603,
              0.0043905603, -0.0107783487, 0.0184915005, 0.0065858404,
             -0.0052223108, 0.0239118633, 0.0087811206, 0.0087811206,
              0.0080202564, 0.0295926259, 0.0237676496, -0.0043905603,
             -0.0043905603, -0.0043905603, -0.0119750148, 0.0026599098,
             -0.0032929202, -0.021005147,  0.022696114])

        np.testing.assert_allclose(filter, filter_ref, rtol=1e-8, atol=1e-9,
            err_msg="In TestFeedforwardFilter, test_1: filter array incorrect")

        del TWC

    def test_2(self):

        TWC = SPS3Section200MHzTWC()
        filter, n_taps, n_filling, n_fit = feedforward_filter(TWC, self.T_s,
            debug=False, opt_output=True)
        self.assertEqual(n_taps, 31,
            msg="In TestFeedforwardFilter, test_2: n_taps incorrect")
        self.assertEqual(n_filling, 18,
            msg="In TestFeedforwardFilter, test_2: n_filling incorrect")
        self.assertEqual(n_fit, 49,
            msg="In TestFeedforwardFilter, test_2: n_fit incorrect")

#        filter_ref = np.array(
#            [-0.0070484734, 0.0161859736, 0.0020289928, 0.0020289928,
#              0.0020289928, -0.0071641302, -0.0162319424, -0.0070388194,
#              0.0020289928, 0.0020289928, 0.0020289928, - 0.0050718734,
#              0.0065971343, 0.0030434892, 0.0030434892, 0.0030434892,
#              0.0030434892, 0.0030434892, -0.0004807475, 0.011136476,
#              0.0040579856, 0.0040579856, 0.0040579856, 0.0132511086,
#              0.019651364, 0.0074147518, -0.0020289928, -0.0020289928,
#             -0.0020289928, -0.0162307252, 0.0071072903])
        filter_ref = np.copy(feedforward_filter_TWC3)

        np.testing.assert_allclose(filter, filter_ref, rtol=1e-8, atol=1e-9,
            err_msg="In TestFeedforwardFilter, test_2: filter array incorrect")

        del TWC

    def test_3(self):

        TWC = SPS4Section200MHzTWC()
        filter, n_taps, n_filling, n_fit = feedforward_filter(TWC, self.T_s,
            debug=False, opt_output=True)
        self.assertEqual(n_taps, 37,
            msg="In TestFeedforwardFilter, test_3: n_taps incorrect")
        self.assertEqual(n_filling, 24,
            msg="In TestFeedforwardFilter, test_3: n_filling incorrect")
        self.assertEqual(n_fit, 61,
            msg="In TestFeedforwardFilter, test_3: n_fit incorrect")

#        filter_ref = np.array(
#            [ 0.0048142895, 0.0035544775, 0.0011144336, 0.0011144336,
#              0.0011144336, -0.0056984584, -0.0122587698, -0.0054458778,
#              0.0011144336, 0.0011144336, 0.0011144336, -0.0001684528,
#             -0.000662115, 0.0016716504, 0.0016716504, 0.0016716504,
#              0.0016716504, 0.0016716504, 0.0016716504, 0.0016716504,
#              0.0016716504, 0.0016716504, 0.0016716504, 0.0016716504,
#              0.0040787952, 0.0034488892, 0.0022288672, 0.0022288672,
#              0.0022288672, 0.0090417593, 0.0146881621, 0.0062036196,
#             -0.0011144336, -0.0011144336, -0.0011144336, -0.0036802064,
#             -0.0046675309])
        filter_ref = np.copy(feedforward_filter_TWC4)

        np.testing.assert_allclose(filter, filter_ref, rtol=1e-8, atol=1e-9,
            err_msg="In TestFeedforwardFilter, test_3: filter array incorrect")

        del TWC

    def test_4(self):

        TWC = SPS5Section200MHzTWC()
        filter, n_taps, n_filling, n_fit = feedforward_filter(TWC, self.T_s,
            debug=False, opt_output=True)
        self.assertEqual(n_taps, 43,
            msg="In TestFeedforwardFilter, test_4: n_taps incorrect")
        self.assertEqual(n_filling, 31,
            msg="In TestFeedforwardFilter, test_4: n_filling incorrect")
        self.assertEqual(n_fit, 74,
            msg="In TestFeedforwardFilter, test_4: n_fit incorrect")

#        filter_ref = np.array(
#            [ 0.0189205535, -0.0105637125, 0.0007262783, 0.0007262783,
#              0.0006531768, -0.0105310359, -0.0104579343, 0.0007262783,
#              0.0007262783, 0.0007262783, 0.0063272331, -0.0083221785,
#              0.0010894175, 0.0010894175, 0.0010894175, 0.0010894175,
#              0.0010894175, 0.0010894175, 0.0010894175, 0.0010894175,
#              0.0010894175, 0.0010894175, 0.0010894175, 0.0010894175,
#              0.0010894175, 0.0010894175, 0.0010894175, 0.0010894175,
#              0.0010894175, 0.0010894175, 0.0010894175, 0.0105496942,
#             -0.0041924387, 0.0014525567, 0.0014525567, 0.0013063535,
#              0.0114011487, 0.0104579343, -0.0007262783, -0.0007262783,
#             -0.0007262783, 0.0104756312, -0.018823192])
        filter_ref = np.copy(feedforward_filter_TWC5)

        np.testing.assert_allclose(filter, filter_ref, rtol=1e-8, atol=1e-9,
            err_msg="In TestFeedforwardFilter, test_4: filter array incorrect")

        del TWC

    #    TWC4 = SPS4Section200MHzTWC()
    #    FF_4 = feedforward_filter(TWC4, 25e-9, debug=True)

    #    TWC5 = SPS5Section200MHzTWC()
    #    FF_5 = feedforward_filter(TWC5, 25e-9, debug=True)


if __name__ == '__main__':

    unittest.main()
