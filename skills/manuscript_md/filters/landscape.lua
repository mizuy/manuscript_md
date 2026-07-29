-- Portrait sections with an isolated landscape block for wide tables in Word (docx).
--
-- In OOXML, w:sectPr on a paragraph defines that *section* (back to the previous
-- break), not the following content. Therefore:
--   1) portrait sectPr before the table  — closes the preceding portrait section
--   2) landscape content (the table)
--   3) landscape sectPr after the table — closes the landscape section
-- The final body sectPr (patched to portrait) covers the rest of the document.
--
-- Usage:
--   ::: landscape
--   | col | col |
--   | --- | --- |
--   | ... | ... |
--   :::

local function sect_pr(orient)
  local pg
  if orient == "landscape" then
    pg = '<w:pgSz w:w="15840" w:h="12240" w:orient="landscape"/>'
  else
    pg = '<w:pgSz w:w="12240" w:h="15840" w:orient="portrait"/>'
  end
  return table.concat({
    pg,
    '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"',
    ' w:header="720" w:footer="720" w:gutter="0"/>',
    '<w:lnNumType w:countBy="1" w:restart="continuous"/>',
  })
end

local function section_break(orient)
  return pandoc.RawBlock(
    "openxml",
    "<w:p><w:pPr><w:sectPr>" .. sect_pr(orient) .. "</w:sectPr></w:pPr></w:p>"
  )
end

function Div(el)
  if el.classes:includes("landscape") then
    local blocks = pandoc.List({ section_break("portrait") })
    for _, block in ipairs(el.content) do
      blocks:insert(block)
    end
    blocks:insert(section_break("landscape"))
    return blocks
  end
end
