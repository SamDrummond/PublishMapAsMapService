import arcpy
import os
import xml.dom.minidom as DOM

workspace = r"c:/arcgis/PublishMapAsMapService"

mxd = arcpy.mapping.MapDocument('Current')
mxd_summary = mxd.summary
mxd_tags = mxd.tags

ags_connection = workspace + r"/asdfa.ags"
service = "BASE_STREETMAP"
sddraft_file = workspace + r"/" + service + ".sddraft"
sd_file = workspace + r"/" + service + ".sd"

is_replace = True

arcpy.AddMessage("Creating SDDraft")
create_map_sddraft = arcpy.mapping.CreateMapSDDraft(mxd, sddraft_file, service, 'ARCGIS_SERVER', ags_connection,
                                                    False, None, mxd_summary,mxd_tags)

arcpy.AddMessage("Analysing SDDraft")
analyse_sddraft = arcpy.mapping.AnalyzeForSD(sddraft_file)

for key in ('messages', 'warnings', 'errors'):
    print "----" + key.upper() + "---"
    values = analyse_sddraft[key]
    for ((message, code), layer_list) in values.iteritems():
        arcpy.AddMessage("    " + message + " (CODE %i)" % code)
        arcpy.AddMessage("       applies to:")
        for layer in layer_list:
            arcpy.AddMessage("              " + layer.name)
        arcpy.AddMessage("")



arcpy.AddMessage("Updating Service Editor Properties")
xml = sddraft_file
doc = DOM.parse(xml)

type_elements = doc.getElementsByTagName('TypeName')

for type_element in type_elements:

    if (type_element.firstChild.nodeValue == "LayerMetadata") and (type_element.parentNode.tagName == 'SVCExtension'):
        arcpy.AddMessage("Found it")
        svc_extension_node = type_element.parentNode
        enabled_node = svc_extension_node.firstChild
        enabled_node_property = enabled_node.firstChild
        enabled_node_property.nodeValue = 'true'

if is_replace:

    new_type = 'esriServiceDefinitionType_Replacement'

    type_elements = doc.getElementsByTagName('Type')

    for type_element in type_elements:
        if type_element.parentNode.tagName == 'SVCManifest':
            if type_element.hasChildNodes():
                    type_element.firstChild.data = new_type

outXML = xml
f = open(outXML, 'w')
doc.writexml(f)
f.close()


arcpy.AddMessage("Staging Service")
stage_service = arcpy.StageService_server(sddraft_file, sd_file)

arcpy.AddMessage("Upload Service Definition")
upload_service_definition = arcpy.UploadServiceDefinition_server(sd_file, ags_connection)

arcpy.AddMessage("Clean up")
os.remove(sd_file)
