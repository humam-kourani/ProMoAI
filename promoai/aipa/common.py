import base64
import os
from tempfile import NamedTemporaryFile


def get_png_url_from_svg(svg_string, parameters=None):
    if parameters is None:
        parameters = {}

    encoding = parameters.get("encoding", "utf-8")

    svg_file_path = NamedTemporaryFile(suffix=".svg")
    svg_file_path.close()
    svg_file_path = svg_file_path.name

    png_file_path = NamedTemporaryFile(suffix=".png")
    png_file_path.close()
    png_file_path = png_file_path.name

    with open(svg_file_path, "w") as svg_file:
        svg_file.write(svg_string)

    os.system("convert " + svg_file_path + " " + png_file_path)

    base64_bytes = base64.b64encode(open(png_file_path, "rb").read())
    base64_string = base64_bytes.decode(encoding)

    return f"data:image/png;base64,{base64_string} "


def reduce_xml_size_using_pm4py(model_xml_string: str) -> str:
    import pm4py

    temp_bpmn = NamedTemporaryFile(suffix=".bpmn")
    temp_bpmn.close()
    temp_bpmn = temp_bpmn.name

    temp_bpmn_2 = NamedTemporaryFile(suffix=".bpmn")
    temp_bpmn_2.close()
    temp_bpmn_2 = temp_bpmn_2.name

    F = open(temp_bpmn, "w")
    F.write(model_xml_string)
    F.close()

    bpmn_graph = pm4py.read_bpmn(temp_bpmn)
    from pm4py.objects.bpmn.exporter import exporter as bpmn_exporter
    bpmn_exporter.apply(bpmn_graph, temp_bpmn_2,
                        parameters={"enble_bpmn_plane_exporting": False, "enable_incoming_outgoing_exporting": False})

    model_xml_string = open(temp_bpmn_2, "r").read()

    return model_xml_string
