from fastapi.openapi.models import Example

Point = Example(
    summary="Point",
    value={
        "geometry": {"type": "Point", "coordinates": [38.976, 45.035]},
        "properties": {"name": "Test point", "type": "Example"},
    },
)

LineString = Example(
    summary="LineString",
    value={
        "geometry": {
            "type": "LineString",
            "coordinates": [
                [38.974, 45.032],
                [38.976, 45.035],
                [38.980, 45.038]
            ]
        },
        "properties": {
            "name": "Test LineString",
            "type": "Example"
        }
    },
)

Polygon = Example(
    summary="Polygon",
    value={
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [38.973, 45.033],
                    [38.979, 45.033],
                    [38.979, 45.037],
                    [38.973, 45.037],
                    [38.973, 45.033]
                ]
            ],
        },
        "properties": {"name": "Test Polygon", "type": "Example"},
    },
)
