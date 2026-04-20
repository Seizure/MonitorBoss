import pyedid
import impl
import base64

edid_blob = impl.get_edid_blob(1)
edid = pyedid.parse_edid(edid_blob)

edid_b64 = base64.b64encode(edid_blob[:128]).decode("utf-8")

print(edid_blob[:128])
