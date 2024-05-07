from contextlib import ExitStack as DoesNotRaise
from test.test_utils import mock_detections
from typing import List, Optional, Union

import numpy as np
import pytest

from supervision.detection.core import Detections
from supervision.geometry.core import Position

PREDICTIONS = np.array(
    [
        [2254, 906, 2447, 1353, 0.90538, 0],
        [2049, 1133, 2226, 1371, 0.59002, 56],
        [727, 1224, 838, 1601, 0.51119, 39],
        [808, 1214, 910, 1564, 0.45287, 39],
        [6, 52, 1131, 2133, 0.45057, 72],
        [299, 1225, 512, 1663, 0.45029, 39],
        [529, 874, 645, 945, 0.31101, 39],
        [8, 47, 1935, 2135, 0.28192, 72],
        [2265, 813, 2328, 901, 0.2714, 62],
    ],
    dtype=np.float32,
)

DETECTIONS = Detections(
    xyxy=PREDICTIONS[:, :4],
    confidence=PREDICTIONS[:, 4],
    class_id=PREDICTIONS[:, 5].astype(int),
)


# Merge test
TEST_MASK = np.zeros((1000, 1000), dtype=bool)
TEST_MASK[300:351, 200:251] = True
TEST_DET_1 = mock_detections(
    xyxy=[[10, 10, 20, 20], [30, 30, 40, 40], [50, 50, 60, 60]],
    mask=[TEST_MASK, TEST_MASK, TEST_MASK],
    confidence=[0.1, 0.2, 0.3],
    class_id=[1, 2, 3],
    tracker_id=[1, 2, 3],
    data={
        "some_key": [1, 2, 3],
        "other_key": [["1", "2"], ["3", "4"], ["5", "6"]],
    },
)
TEST_DET_2 = mock_detections(
    xyxy=[[70, 70, 80, 80], [90, 90, 100, 100]],
    mask=[TEST_MASK, TEST_MASK],
    confidence=[0.4, 0.5],
    class_id=[4, 5],
    tracker_id=[4, 5],
    data={
        "some_key": [4, 5],
        "other_key": [["7", "8"], ["9", "10"]],
    },
)
TEST_DET_1_2 = mock_detections(
    xyxy=[
        [10, 10, 20, 20],
        [30, 30, 40, 40],
        [50, 50, 60, 60],
        [70, 70, 80, 80],
        [90, 90, 100, 100],
    ],
    mask=[TEST_MASK, TEST_MASK, TEST_MASK, TEST_MASK, TEST_MASK],
    confidence=[0.1, 0.2, 0.3, 0.4, 0.5],
    class_id=[1, 2, 3, 4, 5],
    tracker_id=[1, 2, 3, 4, 5],
    data={
        "some_key": [1, 2, 3, 4, 5],
        "other_key": [["1", "2"], ["3", "4"], ["5", "6"], ["7", "8"], ["9", "10"]],
    },
)
TEST_DET_ZERO_LENGTH = mock_detections(
    xyxy=np.empty((0, 4), dtype=np.float32),
    mask=np.empty((0, *TEST_MASK.shape), dtype=bool),
    confidence=[],
    class_id=[],
    tracker_id=[],
    data={
        "some_key": [],
        "other_key": [],
    },
)
TEST_DET_NONE = mock_detections(
    xyxy=np.empty((0, 4), dtype=np.float32),
)
TEST_DET_DIFFERENT_FIELDS = mock_detections(
    xyxy=[[88, 88, 99, 99]],
    mask=[np.logical_not(TEST_MASK)],
    confidence=None,
    class_id=None,
    tracker_id=[9],
    data={"some_key": [9], "other_key": [["11", "12"]]},
)
TEST_DET_DIFFERENT_DATA = mock_detections(
    xyxy=[[88, 88, 99, 99]],
    mask=[np.logical_not(TEST_MASK)],
    confidence=[0.9],
    class_id=[9],
    tracker_id=[9],
    data={
        "never_seen_key": [9],
    },
)


@pytest.mark.parametrize(
    "detections, index, expected_result, exception",
    [
        (
            DETECTIONS,
            DETECTIONS.class_id == 0,
            mock_detections(
                xyxy=[[2254, 906, 2447, 1353]], confidence=[0.90538], class_id=[0]
            ),
            DoesNotRaise(),
        ),  # take only detections with class_id = 0
        (
            DETECTIONS,
            DETECTIONS.confidence > 0.5,
            mock_detections(
                xyxy=[
                    [2254, 906, 2447, 1353],
                    [2049, 1133, 2226, 1371],
                    [727, 1224, 838, 1601],
                ],
                confidence=[0.90538, 0.59002, 0.51119],
                class_id=[0, 56, 39],
            ),
            DoesNotRaise(),
        ),  # take only detections with confidence > 0.5
        (
            DETECTIONS,
            np.array(
                [True, True, True, True, True, True, True, True, True], dtype=bool
            ),
            DETECTIONS,
            DoesNotRaise(),
        ),  # take all detections
        (
            DETECTIONS,
            np.array(
                [False, False, False, False, False, False, False, False, False],
                dtype=bool,
            ),
            Detections(
                xyxy=np.empty((0, 4), dtype=np.float32),
                confidence=np.array([], dtype=np.float32),
                class_id=np.array([], dtype=int),
            ),
            DoesNotRaise(),
        ),  # take no detections
        (
            DETECTIONS,
            [0, 2],
            mock_detections(
                xyxy=[[2254, 906, 2447, 1353], [727, 1224, 838, 1601]],
                confidence=[0.90538, 0.51119],
                class_id=[0, 39],
            ),
            DoesNotRaise(),
        ),  # take only first and third detection using List[int] index
        (
            DETECTIONS,
            np.array([0, 2]),
            mock_detections(
                xyxy=[[2254, 906, 2447, 1353], [727, 1224, 838, 1601]],
                confidence=[0.90538, 0.51119],
                class_id=[0, 39],
            ),
            DoesNotRaise(),
        ),  # take only first and third detection using np.ndarray index
        (
            DETECTIONS,
            0,
            mock_detections(
                xyxy=[[2254, 906, 2447, 1353]], confidence=[0.90538], class_id=[0]
            ),
            DoesNotRaise(),
        ),  # take only first detection by index
        (
            DETECTIONS,
            slice(1, 3),
            mock_detections(
                xyxy=[[2049, 1133, 2226, 1371], [727, 1224, 838, 1601]],
                confidence=[0.59002, 0.51119],
                class_id=[56, 39],
            ),
            DoesNotRaise(),
        ),  # take only first detection by index slice (1, 3)
        (DETECTIONS, 10, None, pytest.raises(IndexError)),  # index out of range
        (DETECTIONS, [0, 2, 10], None, pytest.raises(IndexError)),  # index out of range
        (DETECTIONS, np.array([0, 2, 10]), None, pytest.raises(IndexError)),
        (
            DETECTIONS,
            np.array(
                [True, True, True, True, True, True, True, True, True, True, True]
            ),
            None,
            pytest.raises(IndexError),
        ),
    ],
)
def test_getitem(
    detections: Detections,
    index: Union[int, slice, List[int], np.ndarray],
    expected_result: Optional[Detections],
    exception: Exception,
) -> None:
    with exception:
        result = detections[index]
        assert result == expected_result


@pytest.mark.parametrize(
    "detections_list, expected_result, exception",
    [
        # Nothing
        ([], Detections.empty(), DoesNotRaise()),  # empty detections list
        # Single
        (
            [Detections.empty()],
            Detections.empty(),
            DoesNotRaise(),
        ),  # single empty detections
        (
            [TEST_DET_1],
            TEST_DET_1,
            DoesNotRaise(),
        ),  # single detection with fields
        (
            [TEST_DET_NONE],
            TEST_DET_NONE,
            DoesNotRaise(),
        ),  # Single weakly-defined detection
        # Similar
        (
            [Detections.empty(), Detections.empty()],
            Detections.empty(),
            DoesNotRaise(),
        ),  # Two empty
        (
            [TEST_DET_1, TEST_DET_2],
            TEST_DET_1_2,
            DoesNotRaise(),
        ),  # Fields with same keys
        # Fields and empty
        (
            [TEST_DET_1, Detections.empty()],
            TEST_DET_1,
            DoesNotRaise(),
        ),  # single detection with fields
        (
            [
                TEST_DET_1,
                TEST_DET_ZERO_LENGTH,
            ],
            TEST_DET_1,
            DoesNotRaise(),
        ),  # Single detection and empty-array fields
        (
            [
                TEST_DET_1,
                TEST_DET_NONE,
            ],
            TEST_DET_1,
            DoesNotRaise(),
        ),  # Single detection and None fields (+ missing Dict keys)
        # Errors: Non-zero-length differently defined keys & data
        (
            [TEST_DET_1, TEST_DET_DIFFERENT_FIELDS],
            None,
            pytest.raises(ValueError),
        ),  # Non-empty detections with different fields
        (
            [TEST_DET_1, TEST_DET_DIFFERENT_DATA],
            None,
            pytest.raises(ValueError),
        ),  # Non-empty detections with different data keys
    ],
)
def test_merge(
    detections_list: List[Detections],
    expected_result: Optional[Detections],
    exception: Exception,
) -> None:
    with exception:
        result = Detections.merge(detections_list=detections_list)
        assert result == expected_result


@pytest.mark.parametrize(
    "detections, anchor, expected_result, exception",
    [
        (
            Detections.empty(),
            Position.CENTER,
            np.empty((0, 2), dtype=np.float32),
            DoesNotRaise(),
        ),  # empty detections
        (
            mock_detections(xyxy=[[10, 10, 20, 20]]),
            Position.CENTER,
            np.array([[15, 15]], dtype=np.float32),
            DoesNotRaise(),
        ),  # single detection; center anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.CENTER,
            np.array([[15, 15], [25, 25]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; center anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.CENTER_LEFT,
            np.array([[10, 15], [20, 25]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; center left anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.CENTER_RIGHT,
            np.array([[20, 15], [30, 25]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; center right anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.TOP_CENTER,
            np.array([[15, 10], [25, 20]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; top center anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.TOP_LEFT,
            np.array([[10, 10], [20, 20]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; top left anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.TOP_RIGHT,
            np.array([[20, 10], [30, 20]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; top right anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.BOTTOM_CENTER,
            np.array([[15, 20], [25, 30]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; bottom center anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.BOTTOM_LEFT,
            np.array([[10, 20], [20, 30]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; bottom left anchor
        (
            mock_detections(xyxy=[[10, 10, 20, 20], [20, 20, 30, 30]]),
            Position.BOTTOM_RIGHT,
            np.array([[20, 20], [30, 30]], dtype=np.float32),
            DoesNotRaise(),
        ),  # two detections; bottom right anchor
    ],
)
def test_get_anchor_coordinates(
    detections: Detections,
    anchor: Position,
    expected_result: np.ndarray,
    exception: Exception,
) -> None:
    result = detections.get_anchors_coordinates(anchor)
    with exception:
        assert np.array_equal(result, expected_result)


@pytest.mark.parametrize(
    "detections_a, detections_b, expected_result",
    [
        (
            Detections.empty(),
            Detections.empty(),
            True,
        ),  # empty detections
        (
            mock_detections(xyxy=[[10, 10, 20, 20]]),
            mock_detections(xyxy=[[10, 10, 20, 20]]),
            True,
        ),  # detections with xyxy field
        (
            mock_detections(xyxy=[[10, 10, 20, 20]], confidence=[0.5]),
            mock_detections(xyxy=[[10, 10, 20, 20]], confidence=[0.5]),
            True,
        ),  # detections with xyxy, confidence fields
        (
            mock_detections(xyxy=[[10, 10, 20, 20]], confidence=[0.5]),
            mock_detections(xyxy=[[10, 10, 20, 20]]),
            False,
        ),  # detection with xyxy field + detection with xyxy, confidence fields
        (
            mock_detections(xyxy=[[10, 10, 20, 20]], data={"test": [1]}),
            mock_detections(xyxy=[[10, 10, 20, 20]], data={"test": [1]}),
            True,
        ),  # detections with xyxy, data fields
        (
            mock_detections(xyxy=[[10, 10, 20, 20]], data={"test": [1]}),
            mock_detections(xyxy=[[10, 10, 20, 20]]),
            False,
        ),  # detection with xyxy field + detection with xyxy, data fields
        (
            mock_detections(xyxy=[[10, 10, 20, 20]], data={"test_1": [1]}),
            mock_detections(xyxy=[[10, 10, 20, 20]], data={"test_2": [1]}),
            False,
        ),  # detections with xyxy, and different data field names
        (
            mock_detections(xyxy=[[10, 10, 20, 20]], data={"test_1": [1]}),
            mock_detections(xyxy=[[10, 10, 20, 20]], data={"test_1": [3]}),
            False,
        ),  # detections with xyxy, and different data field values
    ],
)
def test_equal(
    detections_a: Detections, detections_b: Detections, expected_result: bool
) -> None:
    assert (detections_a == detections_b) == expected_result
