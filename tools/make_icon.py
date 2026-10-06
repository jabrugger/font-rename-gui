"""Generate the repository's original typographic icon at Windows sizes."""
from pathlib import Path
from PySide6.QtCore import QByteArray
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
import struct

ROOT = Path(__file__).resolve().parents[1]
svg = b'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
<rect x="4" y="4" width="248" height="248" rx="48" fill="#171c23"/>
<rect x="20" y="20" width="216" height="216" rx="34" fill="none" stroke="#e2b97b" stroke-width="5"/>
<path d="M62 54H198V103H181V77H105V119H155V103H173V158H155V142H105V179H133V201H62V179H80V77H62Z" fill="#e2b97b"/>
</svg>'''
assets = ROOT/'assets'
assets.mkdir(exist_ok=True)
(assets/'font-renamer.svg').write_bytes(svg)
renderer = QSvgRenderer(QByteArray(svg))
images=[]
for size in (16,24,32,48,64,128,256):
    image = QImage(size,size,QImage.Format.Format_ARGB32)
    image.fill(0)
    painter = QPainter(image)
    renderer.render(painter)
    painter.end()
    from PySide6.QtCore import QBuffer, QIODevice
    buffer=QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer,'PNG')
    images.append((size,bytes(buffer.data())))
offset=6+16*len(images)
header=struct.pack('<HHH',0,1,len(images))
entries=[]
for size,data in images:
    entries.append(struct.pack('<BBBBHHII',size%256,size%256,0,0,1,32,len(data),offset))
    offset+=len(data)
(assets/'font-renamer.ico').write_bytes(header+b''.join(entries)+b''.join(data for _,data in images))
