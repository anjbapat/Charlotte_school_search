import pandas as pd

from components.school_compare import _niche_school_url


def test_niche_url_uses_existing_school_name_and_city():
    school=pd.Series({"school_name":"Bailey Middle School","school_level":"Middle","city":"Cornelius","state":"NC"})

    assert _niche_school_url(school)=="https://www.niche.com/k12/bailey-middle-school-cornelius-nc/"


def test_niche_url_expands_short_k8_school_name():
    school=pd.Series({"school_name":"Ashley Park","school_level":"K-8","city":"Charlotte","state":"NC"})

    assert _niche_school_url(school)=="https://www.niche.com/k12/ashley-park-elementary-school-charlotte-nc/"


def test_niche_url_expands_short_k8_school_name_with_gis_county_city():
    school=pd.Series({
        "school_name":"Ashley Park",
        "school_level":"Elementary",
        "city":"Mecklenburg County",
        "state":"NC",
        "address":"2401 BELFAST DR CHARLOTTE NC 28208",
    })

    assert _niche_school_url(school)=="https://www.niche.com/k12/ashley-park-elementary-school-charlotte-nc/"


def test_niche_url_expands_short_high_school_name_with_gis_county_city():
    school=pd.Series({
        "school_name":"Ardrey Kell",
        "school_level":"High",
        "city":"Mecklenburg County",
        "state":"NC",
        "address":"10220 ARDREY KELL RD CHARLOTTE NC 28277",
    })

    assert _niche_school_url(school)=="https://www.niche.com/k12/ardrey-kell-high-school-charlotte-nc/"


def test_niche_url_uses_known_niche_name_override():
    school=pd.Series({
        "school_name":"Butler High School",
        "school_level":"High",
        "city":"Mecklenburg County",
        "state":"NC",
        "address":"1810 MATTHEWS MINT HILL RD MATTHEWS NC 28105",
    })

    assert _niche_school_url(school)=="https://www.niche.com/k12/david-w-butler-high-school-matthews-nc/"


def test_niche_url_extracts_non_charlotte_city_from_address():
    school=pd.Series({
        "school_name":"Bailey Middle School",
        "school_level":"Middle",
        "city":"Mecklenburg County",
        "state":"NC",
        "address":"11900 BAILEY RD CORNELIUS NC 28031",
    })

    assert _niche_school_url(school)=="https://www.niche.com/k12/bailey-middle-school-cornelius-nc/"


def test_niche_url_keeps_full_middle_school_name():
    school=pd.Series({"school_name":"Alexander Graham Middle School","school_level":"Middle","city":"Charlotte","state":"NC"})

    assert _niche_school_url(school)=="https://www.niche.com/k12/alexander-graham-middle-school-charlotte-nc/"
