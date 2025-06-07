import xml.etree.ElementTree as ET
from io import StringIO

def get_simplified_xml_abstraction(bpmn_content):
    
    root = ET.fromstring(bpmn_content)
    output = StringIO()

    def display_element(element, indent=0):

        indent_str = ' ' * indent
        elem_type = element.tag.split('}')[-1]
        elem_id = element.get('id')
            
        label = None 
        if element.get('name'):
            elm_name = ' '.join(element.get('name').strip().split())
            if len(elm_name) > 0:
                label = elm_name

        if element.text:
            elm_text = ' '.join(element.text.strip().split())
            if len(elm_text) > 0:
                if label:
                    label = label + " | " + elm_text
                else:
                    label = elm_text 

        # leaf_substrings = ['event', 'flow', 'task', 'gateway', 'association']
        attrs_to_exclude = ['type', 'id', 'targetNamespace', 'name', 'exporter', 'exporterVersion', 'isExecutable']
        children_to_exclude = ['incoming', 'outgoing']

        # def is_leaf(element_type):
        #     return any(sub in element_type.lower() for sub in leaf_substrings)
        
        attr_keys = [key for key in element.attrib.keys() if key not in attrs_to_exclude]
        children = [child for child in element if child.tag.split('}')[-1] not in children_to_exclude and child.tag.startswith('{http://www.omg.org/spec/BPMN/20100524/MODEL}')]
        
        # if len(attr_keys) > 0 or (not is_leaf(elem_type) and list(element)):      
        if len(attr_keys) > 0 or len(children) > 0: 
            # Hierarchical representation       
            id = " " + elem_id if elem_id else ""
            name = f" ({label})" if label else ""
            output.write(f"{indent_str}<{elem_type}{id}>" + name)
            output.write("\n")
            for attr, value in element.attrib.items():
                if attr not in attrs_to_exclude:
                    output.write(f"{indent_str}  - {attr}: {value}")
                    output.write("\n")
            for child in children:
                display_element(child, indent + 4)              
                        
            output.write(f"{indent_str}</{elem_type}>")
            output.write("\n")
        else:
            # Flat representation
            id = " " + elem_id if elem_id else ""
            name = f" ({label})" if label else ""
            output.write(f"{indent_str}<{elem_type}{id}" + name + '/>')
            output.write("\n")

    # Begin processing from the root element
    display_element(root)
    return output.getvalue()