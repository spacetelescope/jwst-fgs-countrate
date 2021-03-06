import warnings

import numpy as np
import pandas as pd
import pytest

import fgscountrate
from fgscountrate.fgs_countrate_core import FGSCountrate


test_query_fgs_countrate_magnitude_parameters = ['GSC242', 'GSC241']
@pytest.mark.parametrize('gsc', test_query_fgs_countrate_magnitude_parameters)
def test_query_fgs_countrate_magnitude(gsc):
    """
    Test this function runs smoothly and doesn't error
    for multiple guide star catalogs
    (not tested anywhere else)
    """

    # A case with all bands/uncertainties present
    gs_id = 'N13I000018'
    guider = 1
    fgs = FGSCountrate(guide_star_id=gs_id, guider=guider)
    cr, cr_err, mag, mag_err = fgs.query_fgs_countrate_magnitude(catalog=gsc)
    assert cr > 0
    assert mag > 0
    if any(i == -999 for i in fgs._all_queried_mag_series.values):
        warnings.warn('GS ID N13I000018 no longer behaves as originally expected. Test must be updated')

    # A case with missing all 3 tmass bands
    gs_id = 'N94D006388'
    guider = 1
    fgs = FGSCountrate(guide_star_id=gs_id, guider=guider)
    cr, cr_err, mag, mag_err = fgs.query_fgs_countrate_magnitude()
    assert any(fgs.band_dataframe.at[i, 'Signal'] > 0 for i in ['tmassJMag', 'tmassHMag', 'tmassKsMag'])
    assert cr > 0
    assert mag > 0
    if any(i != -999 for i in fgs.gsc_series[['tmassJMag', 'tmassHMag', 'tmassKsMag']].values):
        warnings.warn('GS ID N94D006388 no longer behaves as originally expected. Test must be updated')

    # A case with missing uncertainty data
    gs_id = 'N13I018276'
    guider = 1
    fgs = FGSCountrate(guide_star_id=gs_id, guider=guider)
    cr, cr_err, mag, mag_err = fgs.query_fgs_countrate_magnitude()
    assert fgs.k_mag_err > 0  # this value should get reset
    assert cr > 0
    assert mag > 0
    if fgs.gsc_series['tmassKsMagErr'] != -999:
        warnings.warn('GS ID N13I018276 no longer behaves as originally expected. Test must be updated')


def test_compute_countrate_magnitude():
    """
    Test the conversion from GSC magnitudes to FGS countrate
    returns values as expected
    """

    gs_id = 'N13I000018'
    guider = 1
    fgs = FGSCountrate(guide_star_id=gs_id, guider=guider)

    # Reset data to a set of constant, fake data
    values = ['N13I000018 ', 420900912, 273.206729760604, 65.5335149359777,
              8.3030233068735e-05, 0.000185964552890292, 14.9447, 0.285722,
              14.0877, 0.29279299999999997, 13.7468, 0.239294, 13.33899974823,
              0.025000000372529, 12.9930000305176, 0.0270000007003546,
              12.9010000228882, 0.0270000007003546, 15.78594, 0.005142466,
              14.654670000000001, 0.003211281, 14.27808, 0.0032733809999999997,
              14.14432, 0.003414216, 14.106670000000001, 0.00433389]
    index = ['hstID', 'gsc1ID', 'ra', 'dec', 'raErr', 'decErr',
             'JpgMag', 'JpgMagErr', 'FpgMag', 'FpgMagErr', 'NpgMag', 'NpgMagErr',
             'tmassJMag', 'tmassJMagErr', 'tmassHMag', 'tmassHMagErr', 'tmassKsMag', 'tmassKsMagErr',
             'SDSSuMag', 'SDSSuMagErr', 'SDSSgMag', 'SDSSgMagErr', 'SDSSrMag', 'SDSSrMagErr',
             'SDSSiMag', 'SDSSiMagErr', 'SDSSzMag', 'SDSSzMagErr']
    fgs.gsc_series = pd.Series(values, index=index)

    # Convert to JHK magnitudes
    fgs.j_mag, fgs.j_mag_err, fgs.h_mag, fgs.h_mag_err, fgs.k_mag, fgs.k_mag_err = \
        fgs.calc_jhk_mag(fgs.gsc_series)

    # Compute FGS countrate and magnitude
    cr, cr_err, mag, mag_err = fgs.calc_fgs_cr_mag_and_err()

    assert np.isclose(cr, 1777234.5129574337, 1e-5)
    assert np.isclose(cr_err, 154340.24919027157, 1e-5)
    assert np.isclose(mag, 13.310964314752303, 1e-5)
    assert np.isclose(mag_err, 0.6657930516063038, 1e-5)


def test_convert_cr_to_fgs_mag():
    """Test count rate to magnitude conversion helper function"""
    # Numbers come from case with all bands
    countrate = 1777234.5129574337
    expected_mag = 13.310964314752303
    mag = fgscountrate.convert_cr_to_fgs_mag(countrate, guider=1)
    assert np.isclose(mag, expected_mag, 1e-5)

    # Numbers come from case with missing bands
    countrate = 1815659.5085523769
    expected_mag = 13.28774013985303
    mag = fgscountrate.convert_cr_to_fgs_mag(countrate, guider=1)
    assert np.isclose(mag, expected_mag, 1e-5)


def test_convert_fgs_mag_to_cr():
    """Test magnitude to count rate conversion helper function"""
    # Numbers come from case with all bands
    magnitude = 13.310964314752303
    expected_cr = 1777234.5129574337
    cr = fgscountrate.convert_fgs_mag_to_cr(magnitude, guider=1)
    assert np.isclose(cr, expected_cr, 1)

    # Numbers come from case with missing bands
    magnitude = 13.28774013985303
    expected_cr = 1815659.5085523769
    cr = fgscountrate.convert_fgs_mag_to_cr(magnitude, guider=1)
    assert np.isclose(cr, expected_cr, 1)


def test_gscbj_sdssg_missing():
    """Test that when GSC_B_J and SDSS_g are missing, their signal is set to 0"""

    gs_id = 'N13I000018'
    guider = 1
    fgs = FGSCountrate(guide_star_id=gs_id, guider=guider)

    # Reset data to a set of constant, fake data with GSC_B_J and SDSS_g missing
    values = ['N13I000018', 420900912, 273.207, 65.5335, 8.30302e-05, 0.000185965,
              -999, -999, 14.0877, 0.2927929, 13.7468, 0.239294,
              13.339, 0.0250000003, 12.993, 0.0270000007, 12.901, 0.0270000007,
              15.78594, 0.005142, -999, -999, 14.27808, 0.003273380,
              14.1443, 0.003414216, 14.1067, 0.00433389]
    index = ['hstID', 'gsc1ID', 'ra', 'dec', 'raErr', 'decErr',
             'JpgMag', 'JpgMagErr', 'FpgMag', 'FpgMagErr', 'NpgMag', 'NpgMagErr',
             'tmassJMag', 'tmassJMagErr', 'tmassHMag', 'tmassHMagErr', 'tmassKsMag', 'tmassKsMagErr',
             'SDSSuMag', 'SDSSuMagErr', 'SDSSgMag', 'SDSSgMagErr', 'SDSSrMag', 'SDSSrMagErr',
             'SDSSiMag', 'SDSSiMagErr', 'SDSSzMag', 'SDSSzMagErr']
    fgs.gsc_series = pd.Series(values, index=index)

    # Convert to JHK magnitudes
    fgs.j_mag, fgs.j_mag_err, fgs.h_mag, fgs.h_mag_err, fgs.k_mag, fgs.k_mag_err = \
        fgs.calc_jhk_mag(fgs.gsc_series)

    # Compute FGS countrate and magnitude to get fgs.band_dataframe attribute
    fgs.calc_fgs_cr_mag_and_err()

    # Check Mag, ABMag, and Flux = -999 and Signal is set to 0 for both
    assert fgs.band_dataframe.at['JpgMag', 'Mag'] == -999
    assert fgs.band_dataframe.at['SDSSgMag', 'Mag'] == -999
    assert fgs.band_dataframe.at['JpgMag', 'ABMag'] == -999
    assert fgs.band_dataframe.at['SDSSgMag', 'ABMag'] == -999
    assert fgs.band_dataframe.at['JpgMag', 'Flux'] == -999
    assert fgs.band_dataframe.at['SDSSgMag', 'Flux'] == -999
    assert fgs.band_dataframe.at['JpgMag', 'Signal'] == 0.0
    assert fgs.band_dataframe.at['SDSSgMag', 'Signal'] == 0.0


def test_errors():
    """Test errors are raised properly """

    gs_id = 'N13I000018'
    guider = 1

    # Test 1: data only includes 2MASS
    fgs = FGSCountrate(guide_star_id=gs_id, guider=guider)
    fgs.gsc_series = fgscountrate.utils.query_gsc(gs_id=gs_id, catalog='GSC242').iloc[0]

    fgs._present_calculated_mags = ['tmassJMag', 'tmassHMag', 'tmassKsMag']
    for index in set(fgscountrate.fgs_countrate_core.GSC_BAND_NAMES) - set(fgs._present_calculated_mags):
        fgs.gsc_series.loc[index] = -999
    fgs._all_calculated_mag_series = fgs.gsc_series.loc[fgscountrate.fgs_countrate_core.GSC_BAND_NAMES]

    with pytest.raises(ValueError) as excinfo:
        fgs.calc_fgs_cr_mag_and_err()
    assert 'Cannot compute' in str(excinfo.value), 'Attempted to compute the FGS countrate & ' \
                                                   'magnitude despite only having the 2MASS bands'

    # Test 2: Guider number is invalid
    guider = 3
    with pytest.raises(ValueError) as excinfo:
        fgs = FGSCountrate(guide_star_id=gs_id, guider=guider)
    assert '1 or 2' in str(excinfo.value), 'Allowed invalid guider number to pass'


def test_output_options():
    """
    Test the output options for calc_fgs_cr_mag_and_err()
    and _calc_fgs_cr_mag() are as expected
    """

    gs_id = 'N13I000018'
    guider = 2
    fgs = FGSCountrate(guide_star_id=gs_id, guider=guider)
    fgs.gsc_series = fgscountrate.utils.query_gsc(gs_id=gs_id, catalog='GSC242').iloc[0]
    fgs._present_calculated_mags = fgscountrate.fgs_countrate_core.GSC_BAND_NAMES
    fgs._all_calculated_mag_series = fgs.gsc_series.loc[fgs._present_calculated_mags]
    mag_err_list = [fgs.gsc_series[ind + 'Err'] for ind in fgs._all_calculated_mag_series.index]
    fgs._all_calculated_mag_err_series = pd.Series(mag_err_list, index=fgs._all_calculated_mag_series.index+'Err')

    # Test output from calc_fgs_cr_mag_and_err()
    return_list = fgs.calc_fgs_cr_mag_and_err()
    assert len(return_list) == 4

    # Test output from _calc_fgs_cr_mag()
    band_series = fgs._all_calculated_mag_series
    guider_throughput = fgscountrate.fgs_countrate_core.THROUGHPUT_G2
    guider_gain = fgscountrate.fgs_countrate_core.CR_CONVERSION_G2

    # Case 1: Only Countrate
    return_list = fgs._calc_fgs_cr_mag(to_compute='countrate',
                                       band_series=band_series, guider_throughput=guider_throughput,
                                       guider_gain=guider_gain, return_dataframe=False)
    assert len(return_list) == 1
    assert np.isclose(return_list[0], fgs.fgs_countrate, 1e-5)

    # Case 2: Only Magnitude
    return_list = fgs._calc_fgs_cr_mag(to_compute='magnitude',
                                       band_series=band_series, guider_throughput=guider_throughput,
                                       guider_gain=guider_gain, return_dataframe=False)
    assert len(return_list) == 1
    assert np.isclose(return_list[0], fgs.fgs_magnitude, 1e-5)

    # Case 3: Both
    return_list = fgs._calc_fgs_cr_mag(to_compute='both',
                                       band_series=band_series, guider_throughput=guider_throughput,
                                       guider_gain=guider_gain, return_dataframe=False)
    assert len(return_list) == 2
    assert np.isclose(return_list[0], fgs.fgs_countrate, 1e-5)
    assert np.isclose(return_list[1], fgs.fgs_magnitude, 1e-5)

    # Case 4: Countrate + Dataframe Only
    return_list = fgs._calc_fgs_cr_mag(to_compute='countrate',
                                       band_series=band_series, guider_throughput=guider_throughput,
                                       guider_gain=guider_gain, return_dataframe=True)
    assert len(return_list) == 2
    assert np.isclose(return_list[0], fgs.fgs_countrate, 1e-5)
    np.testing.assert_array_almost_equal(return_list[1].values.flatten().tolist(),
                                         fgs.band_dataframe.values.flatten().tolist(), 5)

    # Case 5: Magnitude + Dataframe Only
    return_list = fgs._calc_fgs_cr_mag(to_compute='magnitude',
                                       band_series=band_series, guider_throughput=guider_throughput,
                                       guider_gain=guider_gain, return_dataframe=True)
    assert len(return_list) == 2
    assert np.isclose(return_list[0], fgs.fgs_magnitude, 1e-5)
    np.testing.assert_array_almost_equal(return_list[1].values.flatten().tolist(),
                                         fgs.band_dataframe.values.flatten().tolist(), 5)

    # Case 6: Countrate, Magnitude, and Dataframe
    return_list = fgs._calc_fgs_cr_mag(to_compute='both',
                                       band_series=band_series, guider_throughput=guider_throughput,
                                       guider_gain=guider_gain, return_dataframe=True)
    assert len(return_list) == 3
    assert np.isclose(return_list[0], fgs.fgs_countrate, 1e-5)
    assert np.isclose(return_list[1], fgs.fgs_magnitude, 1e-5)
    np.testing.assert_array_almost_equal(return_list[2].values.flatten().tolist(),
                                         fgs.band_dataframe.values.flatten().tolist(), 5)
