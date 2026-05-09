# Custom hook to override the broken built-in webrtcvad hook.
# The package is installed as 'webrtcvad-wheels' so its metadata is not
# discoverable under the name 'webrtcvad'. We copy the metadata using the
# correct distribution name instead.
from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata("webrtcvad-wheels")
