import pytest

from tests.conftest import data


async def test_get_feature_collection(ac) -> None:
    response = await ac.get(url="/features")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == data.example_collection_data


@pytest.mark.parametrize(
    "json_data, status_code, _id",
    [
        (data.point_data, 201, 4),
        (data.line_data, 201, 5),
        (data.polygon_data, 201, 6),
        (data.example_collection_data, 422, 0),
    ],
)
async def test_post_features(ac, json_data, status_code, _id) -> None:
    response = await ac.post(url="/features", json=json_data)
    assert response.status_code == status_code
    if status_code == 200:
        response_data = response.json()
        assert response_data == {"id": _id}


@pytest.mark.parametrize(
    "status_code, _id",
    [
        (204, 4),
        (204, 5),
        (204, 6),
        (404, 0),
    ],
)
async def test_delete_features(ac, status_code, _id) -> None:
    response = await ac.delete(url=f"/features/{_id}")
    assert response.status_code == status_code


async def test_get_stats(ac) -> None:
    stats = {"polygons": 1, "lines": 1, "points": 1}
    response = await ac.get(url="/stats")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data == stats
