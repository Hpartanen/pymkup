import os
import pytest
from datetime import datetime

from pymkup import Pymkup
from pymkup.data_conversion import (
    content_hex_convert,
    feet_inches_convert,
    date_string,
    color_to_num,
    tuple_float,
)

_TEST_PDF_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "pymkup", "tests"
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def deep_spaces_pdf():
    return Pymkup(os.path.join(_TEST_PDF_DIR, "markup-deep-spaces.pdf"))


@pytest.fixture
def space_pdf():
    return Pymkup(os.path.join(_TEST_PDF_DIR, "markup-space.pdf"))


@pytest.fixture
def measure_pdf():
    return Pymkup(os.path.join(_TEST_PDF_DIR, "measure.pdf"))


# ── Page Labels ───────────────────────────────────────────────────────────────


class TestPageLabels:
    def test_deep_spaces_has_two_pages(self, deep_spaces_pdf):
        labels = deep_spaces_pdf.get_page_labels()
        assert len(labels) == 2

    def test_deep_spaces_page_labels(self, deep_spaces_pdf):
        labels = deep_spaces_pdf.get_page_labels()
        assert labels[0] == "A101"
        assert labels[1] == "A102"

    def test_space_pdf_has_one_page(self, space_pdf):
        labels = space_pdf.get_page_labels()
        assert len(labels) == 1

    def test_space_pdf_page_label(self, space_pdf):
        labels = space_pdf.get_page_labels()
        assert labels[0] == "Page 1"

    def test_measure_pdf_page_label(self, measure_pdf):
        labels = measure_pdf.get_page_labels()
        assert labels[0] == "Page 1"


# ── Markups List ──────────────────────────────────────────────────────────────


class TestMarkupsList:
    def test_deep_spaces_markup_count(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.get_markups_list()
        assert len(markups) == 13

    def test_space_pdf_markup_count(self, space_pdf):
        markups = space_pdf.get_markups_list()
        assert len(markups) == 26

    def test_measure_pdf_markup_count(self, measure_pdf):
        markups = measure_pdf.get_markups_list()
        assert len(markups) == 10


# ── Markups Index ─────────────────────────────────────────────────────────────


class TestMarkupsIndex:
    def test_deep_spaces_index_maps_all_markups(self, deep_spaces_pdf):
        index = deep_spaces_pdf.get_markups_index()
        assert len(index) == 13

    def test_deep_spaces_index_pages(self, deep_spaces_pdf):
        """First 8 markups on page 0, last 5 on page 1."""
        index = deep_spaces_pdf.get_markups_index()
        page_values = list(index.values())
        assert page_values.count(0) == 8
        assert page_values.count(1) == 5

    def test_measure_pdf_all_on_page_zero(self, measure_pdf):
        index = measure_pdf.get_markups_index()
        assert all(page == 0 for page in index.values())


# ── Columns ───────────────────────────────────────────────────────────────────


class TestColumns:
    def test_deep_spaces_has_subject_column(self, deep_spaces_pdf):
        cols = deep_spaces_pdf.get_columns()
        assert "Subj" in cols
        assert cols["Subj"] == "Subject"

    def test_measure_pdf_has_measurement_columns(self, measure_pdf):
        cols = measure_pdf.get_columns()
        assert "MeasurementTypes" in cols
        assert "SlopeType" in cols
        assert "DepthUnit" in cols

    def test_space_pdf_has_layer_column(self, space_pdf):
        cols = space_pdf.get_columns()
        assert "OC" in cols
        assert cols["OC"] == "Layer"

    def test_columns_returns_dict(self, deep_spaces_pdf):
        cols = deep_spaces_pdf.get_columns()
        assert isinstance(cols, dict)


# ── Spaces ────────────────────────────────────────────────────────────────────


class TestSpaces:
    def test_deep_spaces_returns_dict_with_key(self, deep_spaces_pdf):
        spaces = deep_spaces_pdf.spaces()
        assert "spaces" in spaces

    def test_deep_spaces_hierarchy(self, deep_spaces_pdf):
        spaces = deep_spaces_pdf.spaces()
        # Page 0 has Level 3 > Area B hierarchy
        page_0_spaces = spaces["spaces"][1]
        assert "Level 3" in page_0_spaces
        assert "Area B" in page_0_spaces["Level 3"]

    def test_deep_spaces_nested_rooms(self, deep_spaces_pdf):
        spaces = deep_spaces_pdf.spaces()
        area_b = spaces["spaces"][1]["Level 3"]["Area B"]
        expected_rooms = [
            "Room 302", "Room 303", "Room 304", "Room 305",
            "Hallway 330", "Room 106",
        ]
        for room in expected_rooms:
            assert room in area_b

    def test_deep_spaces_sub_rooms(self, deep_spaces_pdf):
        spaces = deep_spaces_pdf.spaces()
        area_b = spaces["spaces"][1]["Level 3"]["Area B"]
        assert "Sub Room" in area_b["Room 302"]
        assert "Sub Room 2" in area_b["Room 305"]

    def test_deep_spaces_page_two_hierarchy(self, deep_spaces_pdf):
        spaces = deep_spaces_pdf.spaces()
        page_1_spaces = spaces["spaces"][3]
        assert "Level 4" in page_1_spaces
        assert "Area A" in page_1_spaces["Level 4"]
        assert "Room 401" in page_1_spaces["Level 4"]["Area A"]
        assert "Hallway 2" in page_1_spaces["Level 4"]["Area A"]

    def test_space_pdf_hierarchy(self, space_pdf):
        spaces = space_pdf.spaces()
        page_0_spaces = spaces["spaces"][1]
        assert "Level 1" in page_0_spaces
        level_1 = page_0_spaces["Level 1"]
        assert "Area A" in level_1
        assert "Area B" in level_1
        assert "Room 101" in level_1["Area A"]
        assert "Room 102" in level_1["Area A"]
        assert "Room 151" in level_1["Area B"]
        assert "Room 152" in level_1["Area B"]

    def test_measure_pdf_empty_spaces(self, measure_pdf):
        spaces = measure_pdf.spaces()
        assert "spaces" in spaces
        # Page exists but has no space definitions
        assert spaces["spaces"][1] == {}

    def test_spaces_vertices_returns_dict(self, deep_spaces_pdf):
        sv = deep_spaces_pdf.spaces(output="vertices")
        assert isinstance(sv, dict)

    def test_spaces_vertices_has_page_keys(self, deep_spaces_pdf):
        sv = deep_spaces_pdf.spaces(output="vertices")
        assert 0 in sv
        assert 1 in sv


# ── Default Markups ───────────────────────────────────────────────────────────


class TestDefaultMarkups:
    def test_returns_dict_with_markups_key(self, deep_spaces_pdf):
        result = deep_spaces_pdf.markups()
        assert "markups" in result

    def test_deep_spaces_markup_count(self, deep_spaces_pdf):
        result = deep_spaces_pdf.markups()
        assert len(result["markups"]) == 13

    def test_space_pdf_markup_count(self, space_pdf):
        result = space_pdf.markups()
        assert len(result["markups"]) == 26

    def test_measure_pdf_markup_count(self, measure_pdf):
        result = measure_pdf.markups()
        assert len(result["markups"]) == 10


# ── Markup Field Values (deep-spaces) ────────────────────────────────────────


class TestDeepSpacesMarkupValues:
    def test_first_markup_subject(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Subject"] == "Count Measurement"

    def test_first_markup_author(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Author"] == "paul.solin"

    def test_first_markup_color(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Color"] == "#ff0000"

    def test_first_markup_label(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Label"] == "Test Measurement"

    def test_first_markup_page_label(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Page Label"] == "A101"
        assert markups[0]["Page Number"] == 1

    def test_page_two_markup_page_label(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[8]["Page Label"] == "A102"
        assert markups[8]["Page Number"] == 2

    def test_count_measurement_values(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Measurement"] == 1
        assert markups[0]["Measurement Unit"] == "Count"

    def test_creation_date_is_datetime(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert isinstance(markups[0]["Creation Date"], datetime)

    def test_creation_date_value(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Creation Date"] == datetime(2021, 4, 20, 20, 26, 7)

    def test_date_value(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Date"] == datetime(2021, 4, 20, 20, 26, 25)


# ── Markup Spaces Assignment ─────────────────────────────────────────────────


class TestMarkupSpaces:
    def test_deep_spaces_sub_room_assignment(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[0]["Space"] == [
            "Level 3", "Area B", "Room 305", "Sub Room 2"
        ]

    def test_deep_spaces_room_assignment(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[1]["Space"] == ["Level 3", "Area B", "Room 304"]

    def test_deep_spaces_hallway_assignment(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[3]["Space"] == ["Level 3", "Area B", "Hallway 330"]

    def test_deep_spaces_page_two_space(self, deep_spaces_pdf):
        markups = deep_spaces_pdf.markups()["markups"]
        assert markups[8]["Space"] == ["Level 4", "Area A", "Room 401"]

    def test_space_pdf_room_assignment(self, space_pdf):
        markups = space_pdf.markups()["markups"]
        assert markups[15]["Space"] == ["Level 1", "Area A", "Room 101"]
        assert markups[16]["Space"] == ["Level 1", "Area A", "Room 102"]

    def test_space_pdf_area_assignment(self, space_pdf):
        markups = space_pdf.markups()["markups"]
        assert markups[17]["Space"] == ["Level 1", "Area A"]

    def test_space_pdf_empty_space(self, space_pdf):
        markups = space_pdf.markups()["markups"]
        # Check marks on layer 1 are outside spaces
        assert markups[0]["Space"] == []

    def test_measure_pdf_all_empty_spaces(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        for markup in markups:
            assert markup.get("Space", []) == []


# ── Layers ────────────────────────────────────────────────────────────────────


class TestLayers:
    def test_space_pdf_layer_one(self, space_pdf):
        markups = space_pdf.markups()["markups"]
        assert markups[0]["Layer"] == "Test Layer 1"

    def test_space_pdf_layer_two(self, space_pdf):
        markups = space_pdf.markups()["markups"]
        assert markups[15]["Layer"] == "Test Layer 2"


# ── Measurement Types ────────────────────────────────────────────────────────


class TestMeasurements:
    def test_length_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[0]["Subject"] == "Length Measurement"
        assert markups[0]["Measurement"] == pytest.approx(5.4167, abs=0.001)
        assert markups[0]["Measurement Unit"] == "ft' in\""
        assert markups[0]["Comments"] == "5'-5\""

    def test_area_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[1]["Subject"] == "Area Measurement"
        assert markups[1]["Measurement"] == pytest.approx(56.37, abs=0.01)
        assert markups[1]["Measurement Unit"] == "sf"

    def test_polylength_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[2]["Subject"] == "Polylength Measurement"
        assert markups[2]["Measurement"] == pytest.approx(18.9583, abs=0.001)
        assert markups[2]["Measurement Unit"] == "ft' in\""

    def test_perimeter_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[3]["Subject"] == "Perimeter Measurement"
        assert markups[3]["Measurement"] == pytest.approx(22.375, abs=0.001)

    def test_diameter_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[4]["Subject"] == "Diameter Measurement"
        assert markups[4]["Measurement"] == pytest.approx(4.75, abs=0.01)

    def test_radius_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[5]["Subject"] == "Radius Measurement"
        assert markups[5]["Measurement"] == pytest.approx(3.75, abs=0.01)

    def test_second_radius_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[6]["Subject"] == "Radius Measurement"
        assert markups[6]["Measurement"] == pytest.approx(2.3333, abs=0.001)

    def test_angle_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[7]["Subject"] == "Angle Measurement"
        assert markups[7]["Measurement"] == "96.69°"
        assert markups[7]["Measurement Unit"] == "°"

    def test_volume_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[8]["Subject"] == "Volume Measurement"
        assert markups[8]["Measurement"] == pytest.approx(0.0, abs=0.01)
        assert markups[8]["Measurement Unit"] == "cu ft"

    def test_count_measurement(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[9]["Subject"] == "Count Measurement"
        assert markups[9]["Measurement"] == 1
        assert markups[9]["Measurement Unit"] == "Count"

    def test_count_measurement_green(self, measure_pdf):
        markups = measure_pdf.markups()["markups"]
        assert markups[9]["Color"] == "#00ff00"


# ── All Columns Markups ──────────────────────────────────────────────────────


class TestAllColumnsMarkups:
    def test_all_columns_returns_markups(self, deep_spaces_pdf):
        columns = list(deep_spaces_pdf.get_columns().values())
        columns += Pymkup.extended_columns()
        result = deep_spaces_pdf.markups(column_list=columns)
        assert "markups" in result
        assert len(result["markups"]) == 13

    def test_all_columns_returns_markups_space(self, space_pdf):
        columns = list(space_pdf.get_columns().values())
        columns += Pymkup.extended_columns()
        result = space_pdf.markups(column_list=columns)
        assert "markups" in result
        assert len(result["markups"]) == 26

    def test_all_columns_returns_markups_measure(self, measure_pdf):
        columns = list(measure_pdf.get_columns().values())
        columns += Pymkup.extended_columns()
        result = measure_pdf.markups(column_list=columns)
        assert "markups" in result
        assert len(result["markups"]) == 10


# ── Data Conversion Functions ─────────────────────────────────────────────────


class TestFeetInchesConvert:
    def test_five_feet_five_inches(self):
        assert feet_inches_convert("5'-5\"") == pytest.approx(5.4167, abs=0.001)

    def test_three_feet_nine_inches(self):
        assert feet_inches_convert("3'-9\"") == pytest.approx(3.75, abs=0.01)

    def test_eighteen_feet_eleven_and_half(self):
        assert feet_inches_convert("18'-11 1/2\"") == pytest.approx(
            18.9583, abs=0.001
        )

    def test_twenty_two_feet_four_and_half(self):
        assert feet_inches_convert("22'-4 1/2\"") == pytest.approx(
            22.375, abs=0.001
        )

    def test_no_feet_separator(self):
        assert feet_inches_convert("no feet here") == ""


class TestDateString:
    def test_parses_pdf_date(self):
        result = date_string("D:20210420202607-05'00'")
        assert result == datetime(2021, 4, 20, 20, 26, 7)

    def test_returns_datetime(self):
        result = date_string("D:20210420201946-05'00'")
        assert isinstance(result, datetime)


class TestColorToNum:
    def test_red(self):
        assert color_to_num([1, 0, 0]) == "#ff0000"

    def test_green(self):
        assert color_to_num([0, 1, 0]) == "#00ff00"

    def test_blue(self):
        assert color_to_num([0, 0, 1]) == "#0000ff"


class TestTupleFloat:
    def test_converts_to_float_tuples(self):
        result = tuple_float([("1", "2"), ("3", "4")])
        assert result == [(1.0, 2.0), (3.0, 4.0)]

    def test_empty_list(self):
        assert tuple_float([]) == []


class TestContentHexConvert:
    def test_none_returns_none(self):
        assert content_hex_convert(None) is None

    def test_plain_string(self):
        assert content_hex_convert("hello") == "hello"


# ── Error Handling ────────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError, match="PDF file not found"):
            Pymkup("/nonexistent/path/file.pdf")

    def test_invalid_pdf_raises_value_error(self):
        # pytest's own __init__.py is a real file but not a valid PDF
        with pytest.raises(ValueError, match="Failed to parse PDF"):
            Pymkup(os.path.join(_TEST_PDF_DIR, "..", "..", "setup.py"))
