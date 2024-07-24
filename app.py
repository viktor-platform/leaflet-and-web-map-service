from io import StringIO, BytesIO
from pathlib import Path

import lxml

from owslib.wms import WebMapService

import folium
from folium import plugins

from munch import Munch
from requests import RequestException
from viktor import ViktorController, UserError
from viktor.parametrization import (
    ViktorParametrization,
    Text,
    MultiSelectField,
    Step,
    OptionField,
    SetParamsButton,
    TextAreaField,
)
from viktor.result import SetParamsResult
from viktor.views import WebView, WebResult, DataView, DataResult, DataItem, DataGroup

WMS_DEFAULT = "https://service.pdok.nl/wandelnet/regionale-wandelnetwerken/wms/v1_0?version=1.3.0&request=getcapabilities&service=wms"


def _get_layer_options(params: Munch, **kwargs) -> list:
    """Get layer options from connected WMS-layer"""
    layers = []
    if params.wms_details.wms_input:
        try:
            wms = WebMapService(params.wms_details.wms_input, params.wms_details.wms_version)
            layers = list(wms.contents)
        except (RequestException, lxml.etree.XMLSyntaxError):
            pass
    if not layers:
        layers = ["Please enter WMS url and version"]
    return layers


def _validate_wms_details(params: Munch, **kwargs) -> None:
    """Validates the WMS input, before the user is allowed to go to the next step."""
    try:
        WebMapService(params.wms_details.wms_input, params.wms_details.wms_version)
    except (RequestException, lxml.etree.XMLSyntaxError):
        raise UserError("Please enter a valid WMS-url first. Click on the button 'Use sample WMS' for an example.")


def connect_to_WMS(wms_url: str, wms_version: str) -> WebMapService:
    """Connects to the WMS-layers"""
    try:
        wms = WebMapService(wms_url, version=wms_version)
    except RequestException:
        raise UserError("The provided url seems to be incorrect. Please check input for WMS url.")
    except lxml.etree.XMLSyntaxError:
        raise UserError("The provided url does not seem to point at a WMS-layer, please check input for WMS url.")
    return wms


def get_WMS_details(wms: WebMapService) -> dict:
    """Gets the details from the WMS layer, such as the base url, layers and name."""
    base_url = wms.url
    layers = list(wms.contents)
    name = wms.identification.title
    return {"Base url": base_url, "Layers": layers, "Name": name}


class Parametrization(ViktorParametrization):
    """Parametrization for the sample Leaflet app."""

    introduction = Step("Introduction", views=["leaflet_introduction"])
    introduction.welcome_text = Text(
        "# WMS in VIKTOR  \n"
        "Welcome to the WMS app. In this app is shown how WMS layers are added to a VIKTOR app. This is done using the "
        "Python package Folium and Leaflet."
        "  \n"
        "## What is WMS?  \n"
        "A WMS (Web Map Service) layer is a type of GIS data layer that allows users to request and "
        "receive map images over the internet.  \n"
        "The main advantage of a WMS-layer is that it ensures the data is always up-to-date, since the "
        "source of the data is located in one place. Additionally, since WMS is hosted, it is not neceassary to host "
        "it yourself.  \n"
        "  \n"
        " ## Leaflet  \n"
        "WMS layers can be added using the powerful open-source JavaScript library [Leaflet](https://leafletjs.com/). "
        "Some of its features include:  \n"
        "- WMS layers  \n"
        "- Layering  \n"
        "- Advanced drawing tools  \n"
        "- Custom baselayers  \n"
        "- ArcGIS connection \n"
        "- Much more...  \n"
        "  \n"
        "On the right-hand side an example of a Leaflet map is shown.  \n"
        "  \n"
        "**JavaScript? No Python?**  \n"
        "So actually it is possible to create a Leaflet map with only Python, thanks to "
        "[Folium](https://pypi.org/project/folium/). Easy!"
    )

    wms_details = Step("WMS set-up", views=["show_wms_details"], on_next=_validate_wms_details)
    wms_details.text = Text(
        "# WMS set-up  \n"
        "In this step we will gather the information required in order to add your own WMS-layer to your map.  \n"
        "## WMS in Leaflet  \n"
        "In order to add WMS-layers to Leaflet, we need obtain some information from the WMS-layer first. "
        "Luckily, we can all do that within this app, making use of the Python package "
        "[OWSLib](https://pypi.org/project/OWSLib/). "
        "We need to obtain the base url, layer names and set the format. For more information, check out this "
        "[tutorial](https://leafletjs.com/examples/wms/wms.html).  \n"
        "- **Base url**: The base url is the url of the WMS, without the 'getcapabilities' part. \n"
        "- **Layers**: A WMS-layer can contain multiple layers. For example: streets, houses, etc.  \n"
        "- **Format**: The format in which the layer is retrieved. Most common is png.  \n"
        "## WMS input  \n"
        "Please provide the WMS url below. When filled in the base url, layers and name of the WMS layer will appear "
        "on the right-hand side. A sample of a WMS url can be used by clicking on the button below.  \n"
        "  \n"
        "In the Netherlands, [PDOK](https://www.pdok.nl/datasets) is the main provider of public WMS-layers. A lot"
        " of interesting examples can be found on their website. \n"
    )
    wms_details.set_sample_wms = SetParamsButton("Use sample WMS", "set_sample_wms")
    wms_details.wms_input = TextAreaField("WMS url", description="Please enter the WMS url here", flex=100)
    wms_details.wms_version = OptionField(
        "WMS version",
        options=["1.1.1", "1.3.0"],
        default="1.3.0",
        description="Enter the version of the WMS-layer here. The most common version is version 1.3.0",
    )
    wms_details.fmt_format = OptionField(
        "Format",
        options=["image/png", "image/jpeg"],
        default="image/png",
        description="Format of data of the WMS. More options are generally available, but to keep it simple only png "
        "and jpg are included in this app. Default is png.",
    )
    wms_map = Step("Custom WMS", views=["custom_wms_map"], next_label="What's next?")
    wms_map.text = Text(
        "# Custom WMS map  \n"
        "Now everything is set up, the WMS-layer can be added to the map. Just select the layers to display on the map."
        " Wait for the map "
        "to reload and the result should appear on the map. That's it!  \n"
        "  \n"
        "*Note: depending on the WMS-layer you are using, you might need to zoom in or zoom out to see the layer "
        "appear on the map.*"
    )
    wms_map.layer_options = MultiSelectField("Display layers", options=_get_layer_options)

    final_step = Step("What's next", views=["final_step"])


class Controller(ViktorController):
    """Controller for the sample Leaflet app."""

    viktor_enforce_field_constraints = True  # Resolves upgrade instruction https://docs.viktor.ai/sdk/upgrades#U83

    label = "My Entity Type"
    parametrization = Parametrization

    @WebView("Leaflet sample map", duration_guess=1)
    def leaflet_introduction(self, params: Munch, **kwargs) -> WebResult:
        """Create and show a sample leaflet map"""
        m = folium.Map(location=[51.922408, 4.4695292], zoom_start=13)
        folium.TileLayer(
            tiles="https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0/Actueel_ortho25/EPSG:3857/{z}/{x}/{y}.jpeg",
            attr='Kaartgegevens &copy; <a href="https://www.kadaster.nl">Kadaster</a>',
            name="NL luchtfoto 2020",
            overlay=False,
            control=True,
        ).add_to(m)
        folium.TileLayer(
            tiles="https://service.pdok.nl/hwh/luchtfotorgb/wmts/v1_0/2018_ortho25/EPSG:3857/{z}/{x}/{y}.jpeg",
            attr='Kaartgegevens &copy; <a href="https://www.kadaster.nl">Kadaster</a>',
            name="NL luchtfoto 2018",
            overlay=False,
            control=True,
        ).add_to(m)
        folium.TileLayer(
            tiles="https://stamen-tiles-{s}.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.jpg",
            attr='Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/'
            'licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/'
            'copyright">OpenStreetMap</a> contributors',
            name="Watercolor",
            overlay=False,
            control=True,
        ).add_to(m)
        folium.raster_layers.TileLayer(
            tiles="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
            attr='Map data: &copy; <a href="http://www.openseamap.org">OpenSeaMap</a> contributors',
            name="OpenSeaMap",
            overlay=True,
            show=True,
        ).add_to(m)
        folium.raster_layers.TileLayer(
            tiles="https://{s}.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png",
            attr='Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | '
            'Map style: &copy; <a href="https://www.OpenRailwayMap.org">OpenRailwayMap</a> '
            '(<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)',
            name="OpenRailWay",
            overlay=True,
            show=False,
        ).add_to(m)
        folium.raster_layers.WmsTileLayer(
            url="https://service.pdok.nl/rws/vaarwegmarkeringennld/wms/v1_0",
            layers=["markdrijvendrd", "markvastrd"],
            transparent=True,
            control=True,
            fmt="image/png",
            name="Vaarwegmarkeringen WMS",
            overlay=True,
            show=True,
            version="1.3.0",
        ).add_to(m)
        draw = plugins.Draw(export=True)
        draw.add_to(m)
        folium.LayerControl().add_to(m)
        html_result = BytesIO()
        m.save(html_result, close_file=False)
        return WebResult(html=StringIO(html_result.getvalue().decode("utf-8")))

    def set_sample_wms(self, params: Munch, **kwargs) -> SetParamsResult:
        """Fills in the sample WMS to the params"""
        return SetParamsResult({"wms_details": {"wms_input": WMS_DEFAULT}})

    @DataView("WMS details", duration_guess=1)
    def show_wms_details(self, params: Munch, **kwargs) -> DataResult:
        """Shows the details of the WMS layer, such as the base url, layers and the name."""
        if not params.wms_details.wms_input:
            data = DataGroup(DataItem("Pleas enter a WMS url", None))
        else:
            wms = connect_to_WMS(params.wms_details.wms_input, params.wms_details.wms_version)
            wms_details = get_WMS_details(wms)
            data = DataGroup(
                base_url=DataItem("Base url", wms_details["Base url"]),
                layers=DataItem(
                    "Layers",
                    f"{len(wms_details['Layers'])} layers",
                    subgroup=DataGroup(
                        *[
                            DataItem(f"Layer {index}", layer)
                            for index, layer in enumerate(wms_details["Layers"], start=1)
                        ]
                    ),
                ),
                name=DataItem("Name", wms_details["Name"]),
            )
        return DataResult(data)

    @WebView("Custom WMS map", duration_guess=1)
    def custom_wms_map(self, params: Munch, **kwargs) -> WebResult:
        """Creates a map with the WMS-layer, as specified by the user."""
        m = folium.Map(location=[51.922408, 4.4695292], zoom_start=13)
        wms = connect_to_WMS(params.wms_details.wms_input, params.wms_details.wms_version)
        wms_details = get_WMS_details(wms)
        wms_layers = params.wms_map.layer_options
        folium.raster_layers.WmsTileLayer(
            url=wms_details["Base url"],
            layers=wms_layers,
            transparent=True,
            control=True,
            fmt=params.wms_details.fmt_format,
            name=wms_details["Name"],
            overlay=True,
            show=True,
            version=params.wms_details.wms_version,
        ).add_to(m)
        folium.LayerControl().add_to(m)
        html_result = BytesIO()
        m.save(html_result, close_file=False)
        return WebResult(html=StringIO(html_result.getvalue().decode("utf-8")))

    @WebView("What's next?", duration_guess=1)
    def final_step(self, params, **kwargs):
        """Initiates the process of rendering the last step."""
        html_path = Path(__file__).parent / "final_step.html"
        with html_path.open() as f:
            html_string = f.read()
        return WebResult(html=html_string)
