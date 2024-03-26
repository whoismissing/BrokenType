# Author: Mateusz Jurczyk (mjurczyk@google.com)
#
# Copyright 2019 Google LLC
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# https://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import os
import struct
import sys
from fontTools.ttLib import TTFont

# Configuration constants.
GLYPHS_PER_SEGMENT = 50
SEGMENTS_PER_PAGE = 75
GLYPHS_PER_PAGE = SEGMENTS_PER_PAGE * GLYPHS_PER_SEGMENT
PAGE_OBJECT_IDX_START = 100
PAGE_CONTENTS_IDX_START = 200

def main(argv):
  if len(argv) != 3:
    print("Usage: %s <font file> <output .pdf path>" % argv[0])
    sys.exit(1)

  # Obtain the number of glyphs in the font, and calculate the number of necessary pages.
  font = TTFont(argv[1])
  glyph_count = len(font.getGlyphSet())
  print("Glyphs in font: %d" % glyph_count)

  page_count = int(math.ceil(float(glyph_count) / GLYPHS_PER_PAGE))
  print("Generated pages: %d" % page_count)

  # Craft the PDF header.
  pdf_data = b"%PDF-1.1\n"
  pdf_data += b"\n"
  pdf_data += b"1 0 obj\n"
  pdf_data += b"<< /Pages 2 0 R >>\n"
  pdf_data += b"endobj\n"
  pdf_data += b"\n"
  pdf_data += b"2 0 obj\n"
  pdf_data += b"<<\n"
  pdf_data += b"  /Type /Pages\n"
  pdf_data += b"  /Count %d\n" % page_count
  pdf_data += b"  /Kids [ %s ]\n" % b" ".join(map(lambda x:b" %d 0 R" % (PAGE_OBJECT_IDX_START + x), (i for i in range(page_count))))
  pdf_data += b">>\n"
  pdf_data += b"endobj\n"
  pdf_data += b"\n"

  # Construct the page descriptor objects.
  for i in range(page_count):
    pdf_data += b"%d 0 obj\n" % (PAGE_OBJECT_IDX_START + i)
    pdf_data += b"<<\n"
    pdf_data += b"  /Type /Page\n"
    pdf_data += b"  /MediaBox [0 0 612 792]\n"
    pdf_data += b"  /Contents %d 0 R\n" % (PAGE_CONTENTS_IDX_START + i)
    pdf_data += b"  /Parent 2 0 R\n"
    pdf_data += b"  /Resources <<\n"
    pdf_data += b"    /Font <<\n"
    pdf_data += b"      /CustomFont <<\n"
    pdf_data += b"        /Type /Font\n"
    pdf_data += b"        /Subtype /Type0\n"
    pdf_data += b"        /BaseFont /TestFont\n"
    pdf_data += b"        /Encoding /Identity-H\n"
    pdf_data += b"        /DescendantFonts [4 0 R]\n"
    pdf_data += b"      >>\n"
    pdf_data += b"    >>\n"
    pdf_data += b"  >>\n"
    pdf_data += b">>\n"
    pdf_data += b"endobj\n"

  # Construct the font body object.
  with open(argv[1], "rb") as f:
      font_data = f.read()

  pdf_data += b"3 0 obj\n"
  pdf_data += b"<</Subtype /OpenType/Length %d>>stream\n" % len(font_data)
  pdf_data += font_data
  pdf_data += b"\nendstream\n"
  pdf_data += b"endobj\n"
  
  # Construct the page contents objects.
  for i in range(page_count):
    pdf_data += b"%d 0 obj\n" % (PAGE_CONTENTS_IDX_START + i)
    pdf_data += b"<< >>\n"
    pdf_data += b"stream\n"
    pdf_data += b"BT\n"

    for j in range(SEGMENTS_PER_PAGE):
      if i * GLYPHS_PER_PAGE + j * GLYPHS_PER_SEGMENT >= glyph_count:
        break

      pdf_data += b"  /CustomFont 12 Tf\n"
      if j == 0:
        pdf_data += b"  10 775 Td\n"
      else:
        pdf_data += b"  0 -10 Td\n"

      # Example:
      # <00320033003400350036003700380039003a003b003c003d003e003f0040004100420043004400450046004700480049004a004b004c004d004e004f0050005100520053005400550056005700580059005a005b005c005d005e005f0060006100620063> Tj
      glyphs = b"".join(map(lambda x: struct.pack(">H", x), (x for x in range(i * GLYPHS_PER_PAGE + j * GLYPHS_PER_SEGMENT, i * GLYPHS_PER_PAGE + (j + 1) * GLYPHS_PER_SEGMENT))))
      hex_str = "".join(["%02x" % b for b in glyphs]).encode("utf-8")
      pdf_data += b"  <%s> Tj\n" % hex_str

    pdf_data += b"ET\n"
    pdf_data += b"endstream\n"
    pdf_data += b"endobj\n"

  # Construct the descendant font object.
  pdf_data += b"4 0 obj\n"
  pdf_data += b"<<\n"
  pdf_data += b"  /FontDescriptor <<\n"
  pdf_data += b"    /Type /FontDescriptor\n"
  pdf_data += b"    /FontName /TestFont\n"
  pdf_data += b"    /Flags 5\n"
  pdf_data += b"    /FontBBox[0 0 10 10]\n"
  pdf_data += b"    /FontFile3 3 0 R\n"
  pdf_data += b"  >>\n"
  pdf_data += b"  /Type /Font\n"
  pdf_data += b"  /Subtype /OpenType\n"
  pdf_data += b"  /BaseFont /TestFont\n"
  pdf_data += b"  /Widths [1000]\n"
  pdf_data += b">>\n"
  pdf_data += b"endobj\n"

  # Construct the trailer.
  pdf_data += b"trailer\n"
  pdf_data += b"<<\n"
  pdf_data += b"  /Root 1 0 R\n"
  pdf_data += b">>\n"

  # Write the output to disk.
  with open(argv[2], "w+b") as f:
    f.write(pdf_data)

if __name__ == "__main__":
  main(sys.argv)
