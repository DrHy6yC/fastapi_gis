from fastapi.openapi.models import Example

Point = Example(
    summary="Point",
    value={
        "geometry": {
            "type": "Point",
            "coordinates": [30.5, 50.5]
        },
        "properties": {
            "name": "Test point",
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
                    [30.0, 50.0],
                    [31.0, 50.0],
                    [31.0, 51.0],
                    [30.0, 51.0],
                    [30.0, 50.0]
                ]
            ]
        },
        "properties": {
            "name": "Test Polygon",
            "type": "Example"
        }
    },
)