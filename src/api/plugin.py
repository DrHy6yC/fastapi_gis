from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, Response


router = APIRouter(prefix="/plugins", tags=["Плагины"])


@router.get("/plugins.xml", response_class=Response)
def get_plugins_xml():
    plugin_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<plugins>
  <plugin name="SyncPlugin" version="1.0">
    <description>плагин синхронизации</description>
    <about>Берет объекты их АПИ, добавляет новые и удаляет которые удалили со слоя</about>
    <version>1.0</version>
    <qgis_minimum_version>3.40</qgis_minimum_version>
    <qgis_maximum_version>3.99</qgis_maximum_version>
    <file_name>plugin.zip</file_name>
    <download_url>http://localhost/plugins/plugin.zip</download_url>
    <icon>http://localhost/plugins/icon.png</icon>
    <homepage>http://localhost/</homepage>
    <tracker>http://localhost/issues</tracker>
    <repository>http://localhost/plugins/plugins.xml</repository>
    <author_name>Dr.Hy6yC</author_name>
    <author_email>dr.hy6yc@gmail.com</author_email>
    <category>Plugins</category>
    <experimental>false</experimental>
    <deprecated>false</deprecated>
  </plugin>
</plugins>
"""
    return Response(content=plugin_xml, media_type="text/xml")


@router.get("/{file_name}")
def get_plugin_file(file_name: str):
    plugin_path = Path("src/plugins") / file_name
    if plugin_path.exists():
        return FileResponse(plugin_path, media_type="application/zip", filename=file_name)
    return Response(status_code=404, content="Файл не найден")

