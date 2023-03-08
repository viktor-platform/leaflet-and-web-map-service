from io import StringIO, BytesIO

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
    TextField,
    OptionField,
    SetParamsButton,
)
from viktor.result import SetParamsResult
from viktor.views import WebView, WebResult, DataView, DataResult, DataItem, DataGroup

WMS_DEFAULT = "https://service.pdok.nl/wandelnet/regionale-wandelnetwerken/wms/v1_0?version=1.3.0&request=getcapabilities&service=wms"


def _get_layer_options(params, **kwargs):
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


def _validate_wms_details(params, **kwargs):
    try:
        _ = WebMapService(params.wms_details.wms_input, params.wms_details.wms_version)
    except (RequestException, lxml.etree.XMLSyntaxError):
        raise UserError("Please enter a valid WMS-url first. Click on the button 'Use sample WMS' for an example.")


def connect_to_WMS(wms_url, wms_version):
    try:
        wms = WebMapService(wms_url, version=wms_version)
    except RequestException:
        raise UserError("The provided url seems to be incorrect. Please check input for WMS url.")
    except lxml.etree.XMLSyntaxError:
        raise UserError("The provided url does not seem to point at a WMS-layer, please check input for WMS url.")
    return wms


def get_WMS_details(wms):
    base_url = wms.url
    layers = list(wms.contents)
    name = wms.identification.title
    return {"Base url": base_url, "Layers": layers, "Name": name}


class Parametrization(ViktorParametrization):
    introduction = Step("Leaflet", views=["leaflet_introduction"], next_label="WMS set-up")
    introduction.welcome_text = Text(
        "# Leaflet in VIKTOR  \n"
        "Welcome to the Leaflet app. In this app the advantages of leaflet in VIKTOR are "
        "shown. Also, instructions are provided on how to add your own WMS-layer to a "
        "map.  \n "
        "  \n"
        "This app is created for those who want to learn more about creating advanced maps. \n"
        " ## Why leaflet?  \n"
        "[Leaflet](https://leafletjs.com/) is a powerful open-source JavaScript library for "
        "interactive maps. It can be used to create more advanced maps in your app. Some of its "
        "features:  \n"
        "- WMS layers  \n"
        "- Layering  \n"
        "- Custom baselayers  \n"
        "- ArcGIS connection \n"
        "- Much more...  \n"
        "  \n"
        "**JavaScript? No Python?**  \n"
        "So actually it is possible to create a leaflet map with only Python, thanks to "
        "[Folium](https://pypi.org/project/folium/). Easy!"
    )

    wms_details = Step("WMS set-up", views=["show_wms_details"], on_next=_validate_wms_details)
    wms_details.text = Text(
        "# WMS set-up  \n"
        "In this step we will gather the required information to add your own WMS-layer to your map.  \n"
        "## What is WMS?  \n"
        "A WMS (Web Map Service) layer is a type of GIS data layer that allows users to request and "
        "receive map images over the internet.  \n"
        "The main advantage of a WMS-layer is that it ensures the data is always up-to-date, since the "
        "source of the data is located in one place. Additionally, since WMS is hosted, it is not neceassary to host it yourself.  \n"
        "  \n"
        "There are a lot of public WMS-layers available. In the Netherlands, [PDOK](https://www.pdok.nl/datasets) is the main provider of public WMS-layers.  \n"
        "## WMS in Leaflet  \n"
        "In order to add WMS-layers to Leaflet, we need obtain some information from the WMS-layer first. "
        "Luckily, we can all do that within this app, making use of the Python package [OWSLib](https://pypi.org/project/OWSLib/)."
        "We need to obtain the base url, layer names and set the format. For more information, check out the [tutorial](https://leafletjs.com/examples/wms/wms.html).  \n"
        "- **Base url**: The base url is the url of the WMS, without the 'getcapabilities' part. \n"
        "- **Layers**: A WMS-layer can contain multiple layers. For example: streets, houses, etc.  \n"
        "- **Format**: The format in which the layer is retrieved. Most common is png.  \n"
        "## WMS input  \n"
        "Please provide the WMS url below. A sample of a WMS url can be used by clicking on the button below."
    )
    wms_details.set_sample_wms = SetParamsButton("Use sample WMS", "set_sample_wms")
    wms_details.wms_input = TextField("WMS url", description="Please enter the WMS url here", flex=100)
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
        description="Format of data of the WMS. More options are generally available, but to keep it simple only png and jpg are included in this app. Default is png.",
    )
    wms_map = Step("Custom WMS", views=["custom_wms_map"])
    wms_map.text = Text(
        "# Custom WMS map  \n"
        "Now everything is set up, the WMS-layer can be added to the map. Just select the layers to display on the map. Wait for the map "
        "to reload and the result should appear on the map. That's it!  \n"
        "  \n"
        "*Note: depending on the WMS-layer you are using, you might need to zoom in or zoom out to see the layer appear on the map.*"
    )
    wms_map.layer_options = MultiSelectField("Display layers", options=_get_layer_options)


class Controller(ViktorController):
    viktor_enforce_field_constraints = True  # Resolves upgrade instruction https://docs.viktor.ai/sdk/upgrades#U83

    label = "My Entity Type"
    parametrization = Parametrization

    @WebView("Leaflet sample map", duration_guess=1)
    def leaflet_introduction(self, params: Munch, **kwargs) -> WebResult:
        m = folium.Map(location=[51.922408, 4.4695292], zoom_start=13)
        draw = plugins.Draw(export=True)
        draw.add_to(m)
        folium.LayerControl().add_to(m)
        html_result = BytesIO()
        m.save(html_result, close_file=False)
        return WebResult(html=StringIO(html_result.getvalue().decode("utf-8")))

    def set_sample_wms(self, params: Munch, **kwargs):
        return SetParamsResult({"wms_details": {"wms_input": WMS_DEFAULT}})

    @DataView("WMS details", duration_guess=1)
    def show_wms_details(self, params: Munch, **kwargs):
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
